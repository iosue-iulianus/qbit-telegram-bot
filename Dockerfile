FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && pip install --no-cache-dir python-telegram-bot qbittorrent-api \
    && apk del .build-deps

COPY bot.py .

CMD ["python", "-u", "bot.py"]
