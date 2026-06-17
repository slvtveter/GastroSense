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

# Копируем кастомный конфиг nginx для маршрутизации
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
