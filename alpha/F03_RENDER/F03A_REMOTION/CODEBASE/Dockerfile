# OMNIS-WATCH F03A — Remotion Docker
# A DEVELOPPER — adapte de CRUSADER Dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y ffmpeg chromium && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
