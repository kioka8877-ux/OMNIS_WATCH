# OMNIS-WATCH F03A — Remotion Docker Image
# Adapte de CRUSADER Dockerfile
FROM node:20-slim

# Installer FFmpeg et Chromium pour Remotion
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    chromium \
    fonts-liberation \
    fonts-noto-color-emoji \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Variables d'environnement pour Chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV REMOTION_CHROME_EXECUTABLE=/usr/bin/chromium

WORKDIR /app

# Copier package.json et installer les dependances
COPY package.json ./
RUN npm install --production

# Copier le code source
COPY . .

# Creer le dossier OUT
RUN mkdir -p OUT

# Commande par defaut: rendu Remotion
CMD ["npx", "remotion", "render", "src/index.jsx", "OmniComposition", "OUT/video_visuelle.mp4", "--codec", "h264", "--image-format", "jpeg"]
