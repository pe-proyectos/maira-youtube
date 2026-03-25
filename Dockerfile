FROM node:22-slim

RUN apt-get update && apt-get install -y chromium && rm -rf /var/lib/apt/lists/*
RUN npm install -g bun

WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY . .

EXPOSE 3000
CMD ["bunx", "remotion", "studio", "--port", "3000", "--host", "0.0.0.0"]
