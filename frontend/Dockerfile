FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Source is bind-mounted at runtime — no build step needed
EXPOSE 3000
ENV PORT=3000
CMD ["npm", "run", "dev"]
