# Dockerfile (pour popcornhub-web)
FROM python:3.12-slim

WORKDIR /app

# 1. Dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Code de l’appli
COPY app.py config.py ./
COPY routes ./routes
COPY services ./services
COPY templates ./templates
COPY static ./static

EXPOSE 5000

CMD ["python", "app.py"]