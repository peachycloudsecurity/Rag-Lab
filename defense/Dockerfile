FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
# Pre-install CPU-only torch. typing_extensions installed first from PyPI (pre-built wheel)
# so pip does not try to build it from source when using the PyTorch index (missing flit_core there).
RUN pip install --no-cache-dir typing_extensions filelock && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py auth.py notes.py admin.py db.py rag_kb.py ./
COPY templates/ ./templates/
COPY static/ ./static/
RUN mkdir -p uploads data

ENV FLASK_APP=app.py
ENV DEVNOTES_DB=/app/data/devnotes.db
EXPOSE 5000

CMD ["python", "app.py"]
