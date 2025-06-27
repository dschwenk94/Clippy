# Clippy Deployment Guide

This guide covers deploying Clippy with the new `src/` directory structure.

## Local Development

### Using the traditional method:
```bash
python app.py
```

### Using the new setup.py:
```bash
# Install in development mode
pip install -e .

# Run using entry point
clippy-server
```

## Production Deployment

### 1. Using Gunicorn

Create `gunicorn_config.py`:
```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
keepalive = 5
```

Run with:
```bash
gunicorn -c gunicorn_config.py app:app
```

### 2. Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_webapp.txt

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
```

### 3. Using systemd (Linux)

Create `/etc/systemd/system/clippy.service`:
```ini
[Unit]
Description=Clippy YouTube Shorts Generator
After=network.target postgresql.service

[Service]
Type=simple
User=clippy
WorkingDirectory=/opt/clippy
Environment="PATH=/opt/clippy/venv/bin"
ExecStart=/opt/clippy/venv/bin/python /opt/clippy/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Environment Variables

Ensure all deployment scripts use the correct paths:

```bash
# Old imports (if any scripts use them)
# from viral_clipper_complete import VirtualClipGenerator

# New imports
# from src.core.viral_clipper_complete import VirtualClipGenerator
```

### 5. WSGI Configuration

For production WSGI servers, create `wsgi.py`:
```python
import sys
import os

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    app.run()
```

### 6. Nginx Configuration

Example nginx config:
```nginx
server {
    listen 80;
    server_name clippy.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/clippy/static;
        expires 30d;
    }

    client_max_body_size 500M;  # For video uploads
}
```

## Path Updates Required

### Check these files for old import paths:
- Any cron jobs or scheduled tasks
- CI/CD pipelines (.github/workflows, .gitlab-ci.yml, etc.)
- Deployment scripts in `scripts/` directory
- Any external tools that import Clippy modules

### Update imports from:
```python
# Old
from viral_clipper_complete import VirtualClipGenerator
from ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6

# New
from src.core.viral_clipper_complete import VirtualClipGenerator
from src.captions.ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6
```

## Docker Compose Example

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/clippy
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./downloads:/app/downloads
      - ./clips:/app/clips

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=clippy
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine

volumes:
  postgres_data:
```

## Post-Deployment Checklist

- [ ] Verify all imports are using new `src/` paths
- [ ] Test video processing functionality
- [ ] Test caption generation
- [ ] Test YouTube upload integration
- [ ] Check logs for any import errors
- [ ] Verify static files are served correctly
- [ ] Test multi-user functionality (if enabled)

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
1. Ensure PYTHONPATH includes the project root
2. Check that all `__init__.py` files exist in `src/` subdirectories
3. Verify imports use the new `src.module.submodule` format

### Path Issues
Add to the top of your deployment scripts:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```
