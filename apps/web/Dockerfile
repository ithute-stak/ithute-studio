FROM node:22-alpine AS deps
RUN corepack enable
WORKDIR /workspace
COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/document-schema/package.json packages/document-schema/package.json
COPY packages/template-engine/package.json packages/template-engine/package.json
COPY packages/editor/package.json packages/editor/package.json
RUN pnpm install --no-frozen-lockfile

FROM node:22-alpine AS build
RUN corepack enable
WORKDIR /workspace
COPY --from=deps /workspace/node_modules ./node_modules
COPY --from=deps /workspace/apps/web/node_modules ./apps/web/node_modules
COPY --from=deps /workspace/packages ./packages
COPY . .
ARG NEXT_PUBLIC_DOCUMENT_STUDIO_API=http://localhost:8001
ENV NEXT_PUBLIC_DOCUMENT_STUDIO_API=$NEXT_PUBLIC_DOCUMENT_STUDIO_API
RUN pnpm --filter @ithute/document-studio-web build

FROM node:22-alpine AS runner
WORKDIR /workspace
ENV NODE_ENV=production
COPY --from=build /workspace .
EXPOSE 3000
CMD ["sh","-lc","corepack enable && pnpm --filter @ithute/document-studio-web start"]
