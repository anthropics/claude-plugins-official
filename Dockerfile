# COE Pricing Intelligence — Docker Image
FROM mcr.microsoft.com/devcontainers/javascript-node:24-bookworm

ARG HTTPS_PROXY
ARG HTTP_PROXY
ENV HTTPS_PROXY=$HTTPS_PROXY
ENV HTTP_PROXY=$HTTP_PROXY

WORKDIR /app

COPY . .
RUN npm install --strict-ssl=false

CMD ["node", "cli.js", "list"]
