# ── Stage 1: Builder ─────────────────────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

COPY . .

# Build production bundle
RUN npm run build


# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM node:18-alpine AS runtime

WORKDIR /app

# Copy only production artifacts
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

EXPOSE 3000

# Production server (not dev server)
CMD ["npm", "start"]
