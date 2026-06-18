# Stage 1: Build
FROM node:20-alpine as build

WORKDIR /app

# Устанавливаем зависимости
COPY package.json package-lock.json ./
RUN npm ci

# Копируем код и собираем
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Копируем собранные файлы из первого стейджа
COPY --from=build /app/dist /usr/share/nginx/html

# Шаблон конфига nginx - официальный образ автоматически прогоняет файлы из
# /etc/nginx/templates через envsubst при старте контейнера, подставляя
# переменные окружения (только реально заданные - $uri/$host и т.п. внутри
# конфига остаются нетронутыми).
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
ENV BACKEND_ORIGIN=http://backend:8000

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
