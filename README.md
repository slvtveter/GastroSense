# GastroSense

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_API-AI_assistant-8E75B2)

**[English version below ⬇ / Scroll down for English](#english-version)**

GastroSense — дашборд ресторанной аналитики, который я сделал, чтобы попрактиковаться в end-to-end ML-инженерии: не просто обучить модели, а довести их до реального API, реального фронтенда и чат-ассистента, который объясняет результаты человеческим языком.

На входе — сырые данные по заказам (CSV-выгрузки из POS-систем типа iiko или R-Keeper, либо сгенерированные демо-данные), на выходе — три вещи, которые реально интересны владельцу ресторана: прогноз спроса, разбивка меню по прибыльности и анализ комбо/cross-sell, основанный на реальной истории заказов, а не на догадках.

## Живое демо

**[gastrosense-frontend-5viw.onrender.com](https://gastrosense-frontend-5viw.onrender.com)** — демо-данные подгружаются автоматически, ничего настраивать не нужно. ([Документация API](https://gastrosense-backend-oom9.onrender.com/docs))

Оба сервиса работают на бесплатном тарифе Render, поэтому "засыпают" после ~15 минут без запросов — первый запрос после паузы может грузиться 30-60 секунд. Это особенность бесплатного хостинга, не баг.

## Превью

| Прогноз продаж | Меню-инжиниринг | Cross-sales комбо |
|---|---|---|
| ![Прогноз](docs/screenshots/forecast.png) | ![Меню-инжиниринг](docs/screenshots/menu.png) | ![Cross-sales](docs/screenshots/cross_sales.png) |

## Что умеет

**Прогноз продаж.** Обучает четыре модели-кандидата (Ridge, Random Forest, XGBoost, LightGBM) на календарных признаках, лагах и скользящих средних, проверяет их на отложенной выборке через walk-forward validation и выбирает ту, что реально показала себя лучше — без жёстко зашитого единственного алгоритма. Выбранная модель строит рекурсивный прогноз на 7 дней вперёд. В дашборде можно прокручивать историю рядом с прогнозом — от 7 дней до целого года.

**Меню-инжиниринг.** Кластеризует позиции меню на классические BCG-сегменты (Звёзды, Лошадки, Загадки, Собаки) через K-Means по популярности и марже, предварительно стандартизируя оба признака, чтобы один не доминировал над другим просто из-за масштаба.

**Анализ cross-sales / комбо.** Это часть, над которой я больше всего итерировал. Наивный рейтинг "что чаще покупают вместе" легко обманывается редкими позициями — если что-то заказали всего два раза, и оба раза с кофе, это не закономерность, а шум. Поэтому вместо сырой частоты совместных покупок дашборд считает **lift**: во сколько раз чаще две позиции реально покупают вместе по сравнению с тем, что предсказал бы случайный шанс. Lift больше 1x значит реальная синергия, которую стоит продвигать как комбо; lift меньше 1x значит, что товары покупают вместе *реже*, чем предсказал бы случай, даже если технически они иногда встречаются в одном чеке. Пары со слишком малым числом заказов исключаются полностью, чтобы маленькая выборка не выдавала себя за сигнал.

**AI-помощник.** Чат-панель на основе **гибридного RAG-пайплайна** поверх сводок из текущей базы данных плюс документации проекта. Retrieval гибридный: dense-ветка (семантические embeddings от Gemini) ищет по смыслу, sparse-ветка (TF-IDF по символьным n-граммам) добавляет точные лексические совпадения и числа. Их скоры min-max нормализуются и сливаются с весами (dense 0.6, sparse 0.4). Зачем dense вообще нужен: основная аудитория пишет по-русски, а TF-IDF выдаёт против английских чанков почти нулевой скор (нет общих n-грамм) — multilingual embeddings ловят смысл через язык. И наоборот, если sparse-ветка нашла только шум (русский запрос против английских чанков), она гейтится по порогу и зануляется, чтобы не выдавать случайный чанк за релевантный. Если ключа/квоты Gemini нет, система gracefully деградирует обратно к чистому TF-IDF, а не падает. Ответ генерирует Gemini через цепочку фоллбеков на несколько моделей, так что исчерпанная квота одной модели не валит весь ассистент. Если вопрос невозможно закрыть проиндексированными данными, ассистент честно об этом говорит вместо того, чтобы придумывать ответ.

## Немного истории

Первая версия проекта была однофайловым Streamlit-приложением с готовыми демо-пресетами — просто задеплоить бесплатно, но без реального бэкенда, без живого обучения моделей, без базы данных. Она сохранена для истории в [`legacy-streamlit-dashboard/`](legacy-streamlit-dashboard/), но больше не деплоится и не поддерживается. Всё, что описано выше — это текущая версия: настоящий React-фронтенд, который общается с настоящим FastAPI-бэкендом.

## Архитектура

| Слой | Стек |
|---|---|
| Frontend | React, TypeScript, Vite, TailwindCSS, Recharts, TanStack Query |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| База данных | SQLite (WAL) |
| ML Engine | scikit-learn, XGBoost, LightGBM, pandas |
| AI-помощник | Гибридный RAG: dense Gemini embeddings + TF-IDF (без векторной БД), Gemini API |

ML Engine запускается фоновыми задачами после каждой загрузки/сидирования данных — прогнозирование, кластеризация меню и market basket анализ, описанные выше. AI-помощник индексирует сводки из текущей базы данных плюс этот README, строит над ними два индекса (dense + sparse) и передаёт найденный контекст в Gemini. Embeddings пересчитываются только при изменении корпуса (кэш по хешу контента), чтобы не упираться в rate-limit бесплатной квоты.

## Как запустить

Требования: [Docker](https://www.docker.com/) и Docker Compose.

```bash
docker-compose up --build
```

Затем откройте:
- Дашборд: [http://localhost](http://localhost)
- Документация API (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

Реальных данных ресторана в репозитории, конечно, нет — дашборд сам подгружает демо-пресет (по умолчанию Casual Coffee Shop) при первом запуске, либо выберите другой в выпадающем списке слева, или загрузите свой CSV. Сидирование пресета генерирует год синтетической, но реалистичной истории заказов (с недельной сезонностью, трендами, праздниками и зависимостями между позициями в чеке) и запускает обучение моделей в фоне.

## Тесты

```bash
cd backend
pytest
```

Покрывают выбор модели в прогнозировании, кластеризацию меню и поведение чат-агента (гибридный RAG-retrieval, sparse-гейтинг и fallback-цепочку).

---

## English version

**[Русская версия выше ⬆](#gastrosense)**

A restaurant analytics dashboard I built to practice end-to-end ML engineering: not just training models, but shipping them behind a real API, a real frontend, and a chat assistant that can explain the results in plain language.

It takes raw order data (CSV exports from POS systems like iiko or R-Keeper, or generated demo data) and turns it into three things a restaurant owner actually cares about: a demand forecast, a menu profitability breakdown, and a combo/cross-sell analysis grounded in real order history instead of guesswork.

### Live demo

**[gastrosense-frontend-5viw.onrender.com](https://gastrosense-frontend-5viw.onrender.com)** — loads a demo preset automatically, no setup needed. ([API docs](https://gastrosense-backend-oom9.onrender.com/docs))

Both services run on Render's free tier, so they spin down after ~15 minutes idle — the first request after that can take 30-60 seconds to wake up. That's a free-hosting quirk, not a bug.

### Preview

| Sales forecast | Menu engineering | Cross-sales combos |
|---|---|---|
| ![Forecast](docs/screenshots/forecast.png) | ![Menu engineering](docs/screenshots/menu.png) | ![Cross-sales](docs/screenshots/cross_sales.png) |

### What it does

**Sales forecasting.** Trains four candidate models (Ridge, Random Forest, XGBoost, LightGBM) on calendar features, lags, and rolling averages, validates them on held-out data with walk-forward validation, and picks whichever one actually performed best instead of hardcoding a single algorithm. The chosen model then produces a recursive 7-day forecast. The dashboard lets you scroll back through 7 days to a full year of history alongside it.

**Menu engineering.** Clusters every menu item into the classic BCG-style segments (Stars, Workhorses, Puzzles, Dogs) using K-Means on popularity and margin, after standardizing both features so neither dominates the clustering just because of scale.

**Cross-sales / combo analysis.** This is the part I iterated on the most. A naive "what's bought together most often" ranking gets fooled by rare items — if something is only ordered twice and both times paired with coffee, that's not a real pattern, it's noise. So instead of raw co-occurrence, the dashboard computes **lift**: how many times more often two items are actually bought together compared to what random chance alone would predict. Lift above 1x means real synergy worth promoting as a bundle; lift below 1x means the items get ordered together *less* than chance would predict, even if they technically co-occur sometimes. Pairs with too few orders behind them are filtered out entirely so small samples can't fake a signal.

**AI copilot.** A chat panel backed by a **hybrid RAG pipeline** over per-domain summaries of the live database plus the project docs. Retrieval is hybrid: a dense branch (Gemini semantic embeddings) matches on meaning, and a sparse branch (char-n-gram TF-IDF) sharpens exact lexical and number matches. Their scores are min-max normalized and fused with weights (dense 0.6, sparse 0.4). Why dense is there at all: the primary audience writes in Russian, and TF-IDF scores Russian queries against the English data chunks at ~0.0 (no shared n-grams) — multilingual embeddings match across the language gap. Conversely, when the sparse branch finds only noise (a Russian query vs English chunks), it's gated out below a threshold so it can't promote an arbitrary chunk to rank 1. If the Gemini key/quota is unavailable, the system degrades gracefully back to pure TF-IDF instead of breaking. Answers are generated by Gemini through a multi-model fallback chain, so one model hitting its free-tier quota doesn't take the whole assistant down. If a question can't be answered from the indexed data, it says so instead of making something up.

### A note on history

The first version of this project was a single-file Streamlit app with baked-in demo presets — simple to deploy for free, but no real backend, no live model training, no database. It's kept around at [`legacy-streamlit-dashboard/`](legacy-streamlit-dashboard/) for reference, but it's no longer deployed or maintained. Everything described above is the current version: a real React frontend talking to a real FastAPI backend.

### Architecture

| Layer | Stack |
|---|---|
| Frontend | React, TypeScript, Vite, TailwindCSS, Recharts, TanStack Query |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite (WAL) |
| ML Engine | scikit-learn, XGBoost, LightGBM, pandas |
| AI Copilot | Hybrid RAG: dense Gemini embeddings + TF-IDF (no vector DB), Gemini API |

The ML Engine runs as background tasks after every upload/seed — forecasting, menu clustering, and market basket analysis, described above. The AI Copilot indexes rolled-up summaries of the current database plus this README, builds both a dense and a sparse index over them, and hands the retrieved context to Gemini. Embeddings are only recomputed when the corpus changes (hashed by content) to stay within the free-tier rate limit.

### Running it

Requirements: [Docker](https://www.docker.com/) and Docker Compose.

```bash
docker-compose up --build
```

Then open:
- Dashboard: [http://localhost](http://localhost)
- API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

There's no real restaurant's data sitting in this repo, obviously — the dashboard auto-loads a demo preset (Casual Coffee Shop, by default) on first run, or pick a different one from the sidebar dropdown, or upload your own CSV export. Seeding a preset generates a year of synthetic-but-realistic order history (weekly seasonality, trends, holidays, and item co-purchase patterns included) and kicks off model training in the background.

### Tests

```bash
cd backend
pytest
```

Covers the forecaster's model selection, the menu clustering, and the chat agent's hybrid RAG retrieval, sparse gating, and fallback behavior.
