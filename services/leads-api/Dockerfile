FROM node:22-alpine AS build

WORKDIR /app
COPY services/leads-api/package*.json ./services/leads-api/
RUN npm ci --prefix services/leads-api

COPY services/leads-api/tsconfig.json ./services/leads-api/
COPY services/leads-api/src ./services/leads-api/src
COPY packages/trackflow-core ./packages/trackflow-core
RUN npm run build --prefix services/leads-api
RUN npm prune --omit=dev --prefix services/leads-api

FROM node:22-alpine

WORKDIR /app/services/leads-api
COPY --from=build /app/services/leads-api/package*.json ./
COPY --from=build /app/services/leads-api/node_modules ./node_modules
COPY --from=build /app/services/leads-api/dist ./dist

ENV PORT=4000
EXPOSE 4000

CMD ["npm", "start"]
