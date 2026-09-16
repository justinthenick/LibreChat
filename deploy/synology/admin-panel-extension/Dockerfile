ARG UPSTREAM_REF=522e8cd404abba30cfa01b2c0e9353e546c8ff2a

FROM alpine:3.22 AS source
ARG UPSTREAM_REF
RUN apk add --no-cache git python3
RUN git clone --filter=blob:none https://github.com/LibreChat-AI/admin-panel.git /src \
    && git -C /src checkout --detach "$UPSTREAM_REF"
COPY inject.py /tmp/inject.py
RUN python3 /tmp/inject.py
COPY deployment.tsx /src/src/routes/_app/deployment.tsx

FROM oven/bun:1.3.11-alpine AS deps
WORKDIR /app
COPY --from=source /src/package.json /src/bun.lock /src/.npmrc ./
COPY --from=source /src/patches/ patches/
COPY --from=source /src/tools/ tools/
RUN bun install --frozen-lockfile

FROM oven/bun:1.3.11-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules node_modules
COPY --from=source /src/ ./
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=${VITE_BASE_PATH}
ENV NODE_ENV=production
RUN bun run build

FROM oven/bun:1.3.11-alpine AS prod-deps
WORKDIR /app
COPY --from=source /src/package.json /src/bun.lock /src/.npmrc ./
COPY --from=source /src/patches/ patches/
COPY --from=source /src/tools/ tools/
RUN bun install --frozen-lockfile \
    && bun install --frozen-lockfile --production

FROM oven/bun:1.3.11-alpine AS runtime
WORKDIR /app
LABEL org.opencontainers.image.source="https://github.com/justinthenick/LibreChat"
LABEL org.opencontainers.image.description="LibreChat Admin Panel with Synology Deployment control route"
ENV NODE_ENV=production
COPY --from=prod-deps /app/node_modules node_modules
COPY --from=build /app/dist dist
COPY --from=build /app/src/server src/server
COPY --from=source /src/server.ts /src/package.json ./
RUN chown -R bun:bun /app
USER bun
ENV PORT=3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD bun -e "fetch(\`http://localhost:\${process.env.PORT}/health\`).then(r=>{if(!r.ok)throw 1}).catch(()=>process.exit(1))"
EXPOSE 3000
CMD ["bun", "run", "start"]
