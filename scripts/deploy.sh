#!/bin/bash
# Production deployment script

set -e

echo "🚀 Starting production deployment..."

# Check if .env file exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please copy .env.production.example to .env.production and configure it."
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.production.yml build

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.production.yml run --rm web flask db upgrade

# Start services
echo "🎯 Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
curl -f http://localhost/health || exit 1

echo "✅ Deployment complete!"
echo "🌐 Application is running at https://${DOMAIN_NAME}"

# Optional: Set up SSL with Let's Encrypt
if [ "$SETUP_SSL" = "true" ]; then
    echo "🔒 Setting up SSL certificate..."
    docker run --rm \
        -v $(pwd)/ssl:/etc/letsencrypt \
        -v $(pwd)/ssl-challenge:/var/www/certbot \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email ${LETSENCRYPT_EMAIL} \
        --agree-tos \
        --no-eff-email \
        -d ${DOMAIN_NAME}
    
    # Restart nginx to load new certificate
    docker-compose -f docker-compose.production.yml restart nginx
fi