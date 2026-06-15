# Деплой портфолио на Render (бесплатно)

Для витрины достаточно **только дашборда** — демо-данные встроены, MySQL не нужен.

## Шаги

1. Залейте репозиторий на GitHub.
2. Зайдите на [render.com](https://render.com) → **New** → **Blueprint**.
3. Подключите репозиторий — Render подхватит `render.yaml`.
4. В **Environment** задайте переменные:

| Переменная | Пример |
|------------|--------|
| `CONTACT_NAME` | Иван Иванов |
| `CONTACT_TELEGRAM` | @ivan_analytics |
| `CONTACT_EMAIL` | ivan@mail.ru |
| `DEMO_URL` | https://gastrosense-portfolio.onrender.com |

5. После деплоя скопируйте URL сервиса в `DEMO_URL` и передеплойте (опционально).

## Локальный запуск

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

Откройте http://localhost:8501

## PDF для рассылки

1. Откройте демо.
2. Выберите «Кофейня-пекарня Coffee & Bakery».
3. Нажмите **Скачать PDF-отчёт**.
4. Прикрепите файл к сообщению владельцу.

Шаблоны сообщений — в [OUTREACH.md](./OUTREACH.md).
