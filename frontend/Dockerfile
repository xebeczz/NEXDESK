# Frontend — Vite build, served by nginx
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Runtime stage ----
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["/bin/sh", "-c", "export BACKEND_HOST=${BACKEND_HOST:-backend:8000} && envsubst '$BACKEND_HOST' < /etc/nginx/conf.d/default.conf > /tmp/default.conf && cp /tmp/default.conf /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
