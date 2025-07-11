# Use Python 3.11 with Ubuntu base for better multimedia support
FROM python:3.11-bullseye

# Install system dependencies for video/audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libglib2.0-0 \
    libgomp1 \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create directories for clips and temporary files
RUN mkdir -p clips temp uploads

# Copy requirements first for better caching
COPY requirements_webapp.txt requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_webapp.txt

# Install additional packages for production
RUN pip install gunicorn psutil

# Download Whisper models for faster startup
RUN python -c "import whisper; whisper.load_model('base')"

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' clippy
RUN chown -R clippy:clippy /app
USER clippy

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start command
CMD ["python", "app.py"]