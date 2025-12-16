FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Run dev server
# Host is already configured in vite.config.js
CMD ["npm", "run", "dev"]
