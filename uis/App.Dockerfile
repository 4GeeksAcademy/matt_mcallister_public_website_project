FROM node:22-alpine

ARG APP_PATH

# Keep monorepo layout so apps can import ../../packages/* via relative paths.
WORKDIR /workspace

COPY packages ./packages
COPY ${APP_PATH}/package*.json ./${APP_PATH}/

WORKDIR /workspace/${APP_PATH}
RUN npm ci

COPY ${APP_PATH}/ ./

EXPOSE 3000
