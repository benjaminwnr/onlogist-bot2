FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2 \
    libxcomposite1 \
    libxrandr2 \
    libgtk-3-0 \
    libgbm1 \
    libxdamage1 \
    libx11-xcb1 \
    libxshmfence1 \
    ca-certificates \
    wget \
    gnupg \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Start script
CMD ["./entrypoint.sh"]