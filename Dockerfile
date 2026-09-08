FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV NLTK_DATA=/app/nltk_data
RUN python -m nltk.downloader -d /app/nltk_data wordnet omw-1.4

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
