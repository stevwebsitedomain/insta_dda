FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV CHROME_BIN=/usr/bin/chromium
ENV DISPLAY=:99

RUN apt-get update && apt-get install -y \
    chromium \
    wget unzip ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libgtk-3-0 libgbm1 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxrandr2 libappindicator3-1 libdbus-1-3 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE ${PORT}

CMD ["bash", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app --workers 1 --threads 4"]
