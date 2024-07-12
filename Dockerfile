# Dockerfile for scraper
FROM python:3.8-slim

WORKDIR /app
COPY . .


RUN pip install -r requirements.txt

CMD ["python", "scraper.py"]

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]


