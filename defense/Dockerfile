FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# Install CPU-only torch first so pip does not pull the CUDA variant (~1.5 GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py auth.py db.py ./
COPY templates/ ./templates/
RUN mkdir -p data

ENV FLASK_APP=app.py
ENV DEVNOTES_DB=/app/data/devnotes.db
EXPOSE 5000

CMD ["python", "app.py"]
