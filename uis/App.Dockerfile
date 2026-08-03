FROM node:22-alpine

ARG APP_PATH

WORKDIR /app
COPY ${APP_PATH}/package*.json ./
RUN npm ci
COPY ${APP_PATH}/ ./

EXPOSE 3000
