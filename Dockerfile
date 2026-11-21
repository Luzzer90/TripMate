FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITTEBYCODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

RUN mkdir -p uploads data

EXPOSE 8000

CMD [ "unicorn","app:app","--host","0.0.0.0","--port","8000" ]