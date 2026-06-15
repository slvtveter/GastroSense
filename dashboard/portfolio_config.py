import os

# Контакты для витрины — задайте в Render / .env или замените здесь
CONTACT_NAME = os.getenv("CONTACT_NAME", "Илья Сергеев")
CONTACT_TELEGRAM = os.getenv("CONTACT_TELEGRAM", "@asyncslvt")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "ilya141005@gmail.com")
CONTACT_PHONE = os.getenv("CONTACT_PHONE", "+79153885443")

# Ссылка на живое демо (подставится после деплоя на Render)
DEMO_URL = os.getenv("DEMO_URL", "")
