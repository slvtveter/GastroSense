import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from app.logger import logger, log_execution_time
from typing import List, Dict, Any, Optional

# Attempt to import LightGBM / XGBoost; both are optional, RandomForest always works.
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

MODEL_DESCRIPTIONS = {
    "Linear Regression (Ridge)": (
        "Ridge regression fits a straight trend + seasonal pattern through past sales. "
        "Most reliable on short or fairly stable history, where tree models tend to overfit."
    ),
    "Random Forest": (
        "Random Forest averages many decision trees trained on different subsets of past days. "
        "Good at capturing non-linear day-of-week effects without much tuning."
    ),
    "XGBoost": (
        "XGBoost — gradient-boosted decision trees, one of the most widely used algorithms "
        "in real-world forecasting and Kaggle-winning solutions. Needs a bit more data to shine."
    ),
    "LightGBM": (
        "LightGBM — a faster gradient-boosting variant that builds trees leaf-wise. "
        "Similar idea to XGBoost, tends to be quicker on larger datasets."
    ),
}

# In-memory record of the model picked on the last run, surfaced to the API
# so the frontend can explain "how we calculated this" next to the chart.
_last_model_info: Dict[str, Any] = {
    "model": None,
    "description": None,
    "validation_rmse": None,
    "validated_on_days": None,
}


def get_last_model_info() -> Dict[str, Any]:
    return dict(_last_model_info)


def _build_candidate_models(n_train_rows: int) -> Dict[str, Any]:
    """Popular, well-understood regressors to choose between. Hyperparameters
    are scaled down for small training sets so tree models can actually split
    (see the min_child_samples bugfix history on this file) instead of
    defaulting to a near-constant prediction.
    """
    min_leaf_samples = max(1, min(20, n_train_rows // 4))
    candidates: Dict[str, Any] = {
        "Linear Regression (Ridge)": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=100, random_state=42, min_samples_leaf=min_leaf_samples
        ),
    }
    if HAS_XGBOOST:
        candidates["XGBoost"] = xgb.XGBRegressor(
            n_estimators=100, learning_rate=0.05, random_state=42,
            min_child_weight=min_leaf_samples, verbosity=0,
        )
    if HAS_LIGHTGBM:
        candidates["LightGBM"] = lgb.LGBMRegressor(
            n_estimators=100, learning_rate=0.05, random_state=42, verbose=-1,
            min_child_samples=min_leaf_samples, min_split_gain=0.0, num_leaves=7,
        )
    return candidates


def _select_best_model(
    X_train: pd.DataFrame, y_train: pd.Series, n_train_rows: int
) -> tuple[str, Optional[float], Optional[int]]:
    """Walk-forward validation: hold out the most recent days, fit each
    candidate on everything before them, and keep whichever generalizes best.
    Falls back to LightGBM/RandomForest with no validation when there isn't
    enough data to hold any out.
    """
    val_size = min(7, max(2, len(X_train) // 4))
    if len(X_train) <= val_size + 5:
        return ("LightGBM" if HAS_LIGHTGBM else "Random Forest", None, None)

    X_fit, X_val = X_train.iloc[:-val_size], X_train.iloc[-val_size:]
    y_fit, y_val = y_train.iloc[:-val_size], y_train.iloc[-val_size:]

    best_name, best_rmse = None, float("inf")
    for name, model in _build_candidate_models(len(X_fit)).items():
        model.fit(X_fit, y_fit)
        preds = model.predict(X_val)
        rmse = float(np.sqrt(np.mean((y_val.to_numpy() - preds) ** 2)))
        if rmse < best_rmse:
            best_name, best_rmse = name, rmse

    return best_name, round(best_rmse, 2), val_size


@log_execution_time("Time Series Demand Forecasting")
def run_demand_forecast(db: Session, forecast_horizon: int = 7) -> List[Dict[str, Any]]:
    """Query daily sales, pick the best-performing model via validation, and
    forecast revenue and order counts for the next 7 days."""
    # 1. Fetch daily aggregated sales
    sql = """
        SELECT
            DATE(timestamp) as date,
            SUM(total_amount) as revenue,
            COUNT(*) as orders_count
        FROM orders
        GROUP BY DATE(timestamp)
        ORDER BY date
    """
    result = db.execute(text(sql)).fetchall()
    if len(result) < 14:
        logger.warning(f"Insufficient historical data to run forecast. Need >= 14 days, found {len(result)}.")
        return []


    # 2. Convert to DataFrame and reindex to daily frequency
    df = pd.DataFrame(result, columns=["date", "revenue", "orders_count"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Fill missing dates with 0 (essential for correct lag features)
    df = df.asfreq("D", fill_value=0)
    df = df.reset_index()

    # Convert Decimals/Floats
    df["revenue"] = df["revenue"].astype(float)
    df["orders_count"] = df["orders_count"].astype(float)

    # 3. Create target forecast dates
    last_date = df["date"].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_horizon + 1)]

    # Create an extended DataFrame for recursive forecasting
    forecast_df = pd.DataFrame({"date": future_dates})
    forecast_df["revenue"] = np.nan
    forecast_df["orders_count"] = np.nan

    full_df = pd.concat([df, forecast_df], ignore_index=True)

    # 4. Helper function to engineer features
    def engineer_features(data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        # Calendar features
        data["day_of_week"] = data["date"].dt.dayofweek
        data["day_of_month"] = data["date"].dt.day
        data["month"] = data["date"].dt.month
        data["is_weekend"] = data["day_of_week"].isin([4, 5, 6]).astype(int)  # Fri, Sat, Sun

        # Lag features
        for lag in [1, 2, 7]:
            data[f"revenue_lag_{lag}"] = data["revenue"].shift(lag)
            data[f"orders_lag_{lag}"] = data["orders_count"].shift(lag)

        # Rolling features (must shift first to prevent data leakage)
        data["revenue_roll_mean_3"] = data["revenue"].shift(1).rolling(window=3).mean()
        data["revenue_roll_mean_7"] = data["revenue"].shift(1).rolling(window=7).mean()
        data["orders_roll_mean_3"] = data["orders_count"].shift(1).rolling(window=3).mean()
        data["orders_roll_mean_7"] = data["orders_count"].shift(1).rolling(window=7).mean()

        return data

    # 5. Train models recursively
    feature_cols = [
        "day_of_week", "day_of_month", "month", "is_weekend",
        "revenue_lag_1", "orders_lag_1",
        "revenue_lag_2", "orders_lag_2",
        "revenue_lag_7", "orders_lag_7",
        "revenue_roll_mean_3", "orders_roll_mean_3",
        "revenue_roll_mean_7", "orders_roll_mean_7"
    ]

    # We train models on historical data
    hist_end_idx = len(df)

    # Build complete features for the historical part
    df_feat = engineer_features(full_df.iloc[:hist_end_idx])
    train_data = df_feat.dropna(subset=feature_cols).copy()

    X_train = train_data[feature_cols]
    y_revenue = train_data["revenue"]
    y_orders = train_data["orders_count"]

    # Pick whichever popular algorithm generalizes best on held-out recent days,
    # instead of always using the same model regardless of how well it fits this data.
    chosen_name, val_rmse, val_days = _select_best_model(X_train, y_revenue, len(X_train))
    logger.info(
        f"Selected '{chosen_name}' for forecasting "
        f"(validation RMSE: {val_rmse if val_rmse is not None else 'n/a'} over {val_days or 0} days, "
        f"trained on {len(X_train)} historical days)."
    )

    candidates = _build_candidate_models(len(X_train))
    model_rev = candidates[chosen_name]
    model_ord = _build_candidate_models(len(X_train))[chosen_name]

    model_rev.fit(X_train, y_revenue)
    model_ord.fit(X_train, y_orders)

    _last_model_info.update(
        {
            "model": chosen_name,
            "description": MODEL_DESCRIPTIONS.get(chosen_name, ""),
            "validation_rmse": val_rmse,
            "validated_on_days": val_days,
        }
    )

    # Calculate RMSE of the chosen model to compute confidence intervals
    pred_rev_train = model_rev.predict(X_train)
    rmse_rev = np.sqrt(np.mean((y_revenue - pred_rev_train) ** 2))
    logger.info(f"Forecasting models trained successfully. Training RMSE (Revenue): {rmse_rev:.2f} ₽")


    # 6. Autoregressive (recursive) forecasting loop for future dates
    for i in range(forecast_horizon):
        curr_idx = hist_end_idx + i

        # Recalculate features for the current row
        temp_df = engineer_features(full_df.iloc[:curr_idx + 1])
        curr_features = temp_df.iloc[[curr_idx]][feature_cols]

        # Predict revenue and orders
        pred_rev = model_rev.predict(curr_features)[0]
        pred_ord = model_ord.predict(curr_features)[0]

        # Ensure non-negative predictions
        pred_rev = max(0.0, float(pred_rev))
        pred_ord = max(0, int(round(pred_ord)))

        # Store prediction in the main dataframe so it can be used for subsequent lags
        full_df.loc[curr_idx, "revenue"] = pred_rev
        full_df.loc[curr_idx, "orders_count"] = pred_ord

    # 7. Collect results and calculate prediction bounds
    forecast_results = []
    for h in range(1, forecast_horizon + 1):
        idx = hist_end_idx + h - 1
        date_val = full_df.loc[idx, "date"].date()
        pred_rev = full_df.loc[idx, "revenue"]
        pred_ord = int(full_df.loc[idx, "orders_count"])

        # Standard error scales with forecasting horizon: SE = RMSE * sqrt(h).
        # Use an 80% interval (z=1.28) instead of 95% (z=1.96) - the 95% band
        # was too wide to be useful on small demo datasets and dominated the chart.
        se = rmse_rev * np.sqrt(h)
        lower_bound = max(0.0, pred_rev - 1.28 * se)
        upper_bound = pred_rev + 1.28 * se

        forecast_results.append({
            "date": date_val,
            "predicted_revenue": round(pred_rev, 2),
            "predicted_orders": pred_ord,
            "lower_bound_revenue": round(lower_bound, 2),
            "upper_bound_revenue": round(upper_bound, 2)
        })

    return forecast_results
