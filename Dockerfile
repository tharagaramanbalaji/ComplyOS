# ==========================================
# STAGE 1: Build React Frontend UI
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Python Backend & AI Engine Runtime
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install system libraries needed for high-speed C-binding lxml execution
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy & Sentence Transformers weights into container cache
RUN python -m spacy download en_core_web_sm
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy full application codebase
COPY . .

# Copy compiled static frontend UI from Stage 1 into backend directory
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose ASGI port
EXPOSE 8000
ENV PORT=8000

# Run Uvicorn multi-worker production server binding to Render's dynamic $PORT
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 4
