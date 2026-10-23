FROM node:22-bookworm-slim AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN mkdir -p public && npm run build

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates && rm -rf /var/lib/apt/lists/*
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PYTHON_EXECUTABLE=python3 \
    PYTHONUTF8=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RADAR_HOST=0.0.0.0 \
    RADAR_REQUIRE_PYTHON=1 \
    RADAR_ACCOUNT_DB=/var/data/accounts.sqlite3 \
    PORT=10000
COPY --from=build /app/package.json /app/package-lock.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/next.config.ts ./next.config.ts
COPY --from=build /app/public ./public
COPY --from=build /app/data ./data
COPY --from=build /app/src/config ./src/config
COPY --from=build /app/chatbot ./chatbot
COPY --from=build /app/scripts/run.mjs ./scripts/run.mjs
RUN mkdir -p /var/data
EXPOSE 10000
CMD ["node", "scripts/run.mjs"]
