# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install compiler toolchain for package builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies to a local user directory
RUN pip install --user --no-cache-dir -r requirements.txt


# Stage 2: Final lightweight runtime
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy built site-packages from builder
COPY --from=builder /root/.local /root/.local
COPY . .

# Extend system path to locate python dependencies
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000
EXPOSE 8501

CMD ["python", "-m", "uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
