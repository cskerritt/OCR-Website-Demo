#!/bin/bash
# Backup script for production data

set -e

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ocr_backup_${TIMESTAMP}"

echo "🗄️  Starting backup process..."

# Create backup directory
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}

# Backup database
echo "📊 Backing up database..."
docker-compose -f docker-compose.production.yml exec -T db \
    pg_dump -U ocruser ocrdb | gzip > ${BACKUP_DIR}/${BACKUP_NAME}/database.sql.gz

# Backup uploaded files
echo "📁 Backing up uploaded files..."
docker run --rm \
    -v ocr_website_uploads:/data \
    -v ${BACKUP_DIR}/${BACKUP_NAME}:/backup \
    alpine tar czf /backup/uploads.tar.gz -C /data .

# Backup OCR cache (optional)
if [ "$BACKUP_CACHE" = "true" ]; then
    echo "💾 Backing up OCR cache..."
    docker run --rm \
        -v ocr_website_ocr_cache:/data \
        -v ${BACKUP_DIR}/${BACKUP_NAME}:/backup \
        alpine tar czf /backup/ocr_cache.tar.gz -C /data .
fi

# Create backup manifest
echo "📝 Creating backup manifest..."
cat > ${BACKUP_DIR}/${BACKUP_NAME}/manifest.json << EOF
{
    "timestamp": "${TIMESTAMP}",
    "version": "$(git rev-parse HEAD)",
    "files": [
        "database.sql.gz",
        "uploads.tar.gz"$([ "$BACKUP_CACHE" = "true" ] && echo ',\n        "ocr_cache.tar.gz"')
    ]
}
EOF

# Compress entire backup
echo "🗜️  Compressing backup..."
cd ${BACKUP_DIR}
tar czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}/
rm -rf ${BACKUP_NAME}/

# Upload to cloud storage (optional)
if [ "$UPLOAD_TO_S3" = "true" ]; then
    echo "☁️  Uploading to S3..."
    aws s3 cp ${BACKUP_NAME}.tar.gz s3://${S3_BACKUP_BUCKET}/
fi

# Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find ${BACKUP_DIR} -name "ocr_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup complete: ${BACKUP_NAME}.tar.gz"