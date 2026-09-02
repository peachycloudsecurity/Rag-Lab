FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
# Pre-install CPU-only torch so pip does not pull the CUDA variant (~1.5 GB when llm-guard is added)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py auth.py notes.py admin.py db.py rag_kb.py ./
COPY templates/ ./templates/
COPY static/ ./static/
RUN mkdir -p uploads data

ENV FLASK_APP=app.py
ENV DEVNOTES_DB=/app/data/devnotes.db
EXPOSE 5000

CMD ["python", "app.py"]
