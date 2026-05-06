FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY app ./app
COPY scripts ./scripts

# Build the FAISS index inside the container
RUN python scripts/build_index.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
