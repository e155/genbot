FROM python:3.12-slim

# ---- system deps ----
RUN apt-get update && apt-get install -y \
    iputils-ping \
    ca-certificates \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# ---- locale (UTF-8) ----
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# ---- workdir ----
WORKDIR /app

# ---- python deps ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- app code ----
COPY bot.py settings.py ./

# ---- data dir for sqlite ----
VOLUME ["/app/data"]

# ---- default env ----
ENV DB_FILE=/app/data/generator.db

# ---- run ----
CMD ["python", "bot.py"]
