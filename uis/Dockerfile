FROM node:22-alpine

WORKDIR /monorepo/uis

COPY website/package*.json ./website/
COPY backoffice/package*.json ./backoffice/
RUN cd website && npm ci && cd ../backoffice && npm ci

COPY website/ ./website/
COPY backoffice/ ./backoffice/
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 3000 3001

CMD ["sh", "./start.sh"]
