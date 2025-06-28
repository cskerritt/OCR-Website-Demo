# Production Deployment Guide

## Overview

This guide covers deploying the OCR Website application in a production environment with high availability, security, and monitoring.

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificate (or use Let's Encrypt)
- At least 4GB RAM and 20GB storage
- PostgreSQL database (or use included)
- Redis instance (or use included)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/cskerritt/OCR-Website-Demo.git
   cd OCR-Website-Demo
   ```

2. **Configure environment**
   ```bash
   cp .env.production.example .env.production
   # Edit .env.production with your settings
   ```

3. **Deploy**
   ```bash
   ./scripts/deploy.sh
   ```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  Flask App  │────▶│ PostgreSQL  │
│  (Reverse   │     │  (Gunicorn) │     │  Database   │
│   Proxy)    │     └─────────────┘     └─────────────┘
└─────────────┘              │                    
       │                     │           ┌─────────────┐
       │                     └──────────▶│    Redis    │
       │                                 │   (Cache)   │
       ▼                                 └─────────────┘
┌─────────────┐                          
│   Static    │     ┌─────────────┐     ┌─────────────┐
│   Files     │     │   Worker    │────▶│   OCRmyPDF  │
│  (CDN/S3)   │     │  (Celery)   │     │  Processing │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Security Features

### 1. Application Security
- HTTPS enforcement with TLS 1.2+
- Security headers (HSTS, CSP, X-Frame-Options)
- Rate limiting on all endpoints
- SQL injection protection
- XSS protection
- CSRF tokens

### 2. Infrastructure Security
- Non-root Docker containers
- Network isolation
- Secrets management
- Regular security updates

### 3. Data Security
- Encrypted database connections
- Secure session management
- Password hashing with bcrypt
- File upload validation

## Performance Optimization

### 1. Caching Strategy
- Redis for session storage
- File processing cache
- Static file caching with CDN
- Database query optimization

### 2. Scaling Options
```yaml
# Horizontal scaling with Docker Swarm
docker service scale ocr_web=4
docker service scale ocr_worker=8
```

### 3. Load Balancing
- Nginx upstream configuration
- Health check endpoints
- Graceful shutdown handling

## Monitoring & Logging

### 1. Application Monitoring
- Health check endpoint: `/health`
- Sentry error tracking
- Custom metrics with Prometheus
- Grafana dashboards

### 2. Infrastructure Monitoring
```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Monitor resources
docker stats

# Check health
curl https://yourdomain.com/health
```

### 3. Alerts
- Disk space warnings
- Memory usage alerts
- Service availability checks
- Error rate monitoring

## Backup & Recovery

### 1. Automated Backups
```bash
# Run backup
./scripts/backup.sh

# Schedule with cron
0 2 * * * /app/scripts/backup.sh
```

### 2. Restore Process
```bash
# Extract backup
tar xzf ocr_backup_20240628_120000.tar.gz

# Restore database
gunzip -c database.sql.gz | docker-compose exec -T db psql -U ocruser ocrdb

# Restore files
docker run --rm -v ocr_website_uploads:/data -v $(pwd):/backup \
    alpine tar xzf /backup/uploads.tar.gz -C /data
```

## Deployment Scenarios

### 1. Single Server
Use the default `docker-compose.production.yml`

### 2. High Availability
```yaml
# docker-swarm.yml
version: '3.8'
services:
  web:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### 3. Kubernetes
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ocr-website
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ocr-website
  template:
    metadata:
      labels:
        app: ocr-website
    spec:
      containers:
      - name: web
        image: ocr-website:latest
        ports:
        - containerPort: 5000
```

## Cloud Deployments

### AWS
```bash
# ECS deployment
ecs-cli compose --file docker-compose.production.yml up

# Or use Elastic Beanstalk
eb init -p docker ocr-website
eb create production
```

### Google Cloud
```bash
# Cloud Run deployment
gcloud run deploy ocr-website \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

### Azure
```bash
# Container Instances
az container create \
    --resource-group ocr-rg \
    --file docker-compose.production.yml
```

## Maintenance

### 1. Updates
```bash
# Update application
git pull origin main
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

### 2. Database Maintenance
```bash
# Vacuum database
docker-compose exec db psql -U ocruser -c "VACUUM ANALYZE;"

# Backup before major updates
./scripts/backup.sh
```

### 3. Cache Cleanup
```bash
# Clear old cache files
docker-compose exec web python -c "from app import cleanup_old_cache_files; cleanup_old_cache_files()"
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Adjust `GUNICORN_WORKERS`
   - Limit OCR threads
   - Enable swap memory

2. **Slow Processing**
   - Check disk I/O
   - Optimize PDF files
   - Scale worker processes

3. **Database Connection Issues**
   - Check connection pool settings
   - Monitor active connections
   - Review slow query log

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose -f docker-compose.production.yml up
```

## Performance Benchmarks

- **Throughput**: 100+ PDFs/minute (4 workers)
- **Latency**: < 2s for small PDFs
- **Availability**: 99.9% uptime target
- **Storage**: ~1GB per 1000 processed PDFs

## Support

- GitHub Issues: https://github.com/cskerritt/OCR-Website-Demo/issues
- Documentation: This guide
- Monitoring: Check Grafana dashboards

## License

See LICENSE file in the repository.