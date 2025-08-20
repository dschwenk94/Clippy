#!/bin/bash

echo "🎯 Setting up Clippy development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from .env.example"
    echo "📝 Please edit .env with your API keys and configuration"
fi

# Create necessary directories
mkdir -p clips temp uploads

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting development environment..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check if app is running
if curl -f http://localhost:5000 > /dev/null 2>&1; then
    echo "✅ Clippy is running at http://localhost:5000"
else
    echo "⚠️  Services may still be starting. Check logs with: npm run logs"
fi

echo "🎉 Setup complete!"
echo ""
echo "📚 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Place your YouTube client_secrets.json in the root directory"
echo "3. Run 'npm run logs' to see application logs"
echo "4. Visit http://localhost:5000 to start using Clippy"