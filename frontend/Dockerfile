# syntax=docker/dockerfile:1.7
# Frontend de Hotel Kawari: build de Vite servido por Nginx, que además hace de proxy de /api y
# /static/uploads hacia la API (mismo origen, requisito de la cookie de sesión SameSite).
#   docker build -t kawari-web frontend

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY . .
# Vacío = la API está en el mismo origen (proxy de Nginx). Solo cambiar si la API vive en otro dominio.
ARG VITE_API_URL=""
ARG VITE_HOTEL_TIMEZONE="America/Bogota"
ARG VITE_CURRENCY="COP"
ENV VITE_API_URL=$VITE_API_URL \
    VITE_HOTEL_TIMEZONE=$VITE_HOTEL_TIMEZONE \
    VITE_CURRENCY=$VITE_CURRENCY
RUN npm run build

# Imagen de Nginx sin root (escucha en 8080)
FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
