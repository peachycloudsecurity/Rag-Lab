FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py auth.py notes.py admin.py db.py rag_kb.py ./
COPY templates/ ./templates/
RUN mkdir -p uploads data

ENV FLASK_APP=app.py
ENV DEVNOTES_DB=/app/data/devnotes.db
EXPOSE 5000

CMD ["python", "app.py"]
