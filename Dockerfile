# Dockerfile for scraper
FROM python:3.8-slim

WORKDIR /app
COPY . .


RUN pip install requests beautifulsoup4 kafka-python fastapi uvicorn

CMD ["python", "scraper.py"]

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]


