FROM node:20-alpine

WORKDIR /usr/src/app

# Install dependencies
COPY package*.json ./
RUN npm ci --silent

# Copy source
COPY . .

EXPOSE 5173

# Use vite dev for local development (hot reload)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
