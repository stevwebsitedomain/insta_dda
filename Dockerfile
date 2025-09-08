# Base image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV CHROME_BIN=/usr/bin/chromium
ENV DISPLAY=:99

# Install system dependencies + Chromium + driver
RUN apt-get update && apt-get install -y \
    wget gnupg2 ca-certificates unzip \
    fonts-liberation libnss3 libxss1 libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libgtk-3-0 libgbm1 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxrandr2 libappindicator3-1 libdbus-1-3 curl chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app source code
COPY . .

# Expose port
EXPOSE ${PORT}

# Start the app using Gunicorn
CMD ["bash", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app --workers 1 --threads 4"]
