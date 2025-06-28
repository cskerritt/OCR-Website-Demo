#!/bin/bash
# Health monitoring script

# Configuration
HEALTH_CHECK_URL="http://localhost/health"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL}"
CHECK_INTERVAL=300  # 5 minutes

# Function to send alert
send_alert() {
    local message=$1
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 OCR Website Alert: ${message}\"}" \
            $SLACK_WEBHOOK_URL
    fi
    echo "[$(date)] ALERT: ${message}" >> /var/log/ocr_monitoring.log
}

# Function to check service health
check_health() {
    response=$(curl -s -w "\n%{http_code}" $HEALTH_CHECK_URL)
    http_code=$(tail -n1 <<< "$response")
    body=$(head -n-1 <<< "$response")
    
    if [ "$http_code" != "200" ]; then
        send_alert "Health check failed with HTTP ${http_code}"
        return 1
    fi
    
    # Check disk space
    disk_usage=$(df -h /app/uploads | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $disk_usage -gt 90 ]; then
        send_alert "Disk usage critical: ${disk_usage}%"
    fi
    
    # Check memory usage
    memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" ocr-website_web_1 | sed 's/%//')
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        send_alert "Memory usage critical: ${memory_usage}%"
    fi
    
    return 0
}

# Main monitoring loop
echo "Starting health monitoring..."
while true; do
    if ! check_health; then
        # Try to restart the service
        echo "Attempting to restart services..."
        docker-compose -f docker-compose.production.yml restart web
        sleep 30
        
        # Check again
        if ! check_health; then
            send_alert "Service restart failed - manual intervention required"
        else
            send_alert "Service recovered after restart"
        fi
    fi
    
    sleep $CHECK_INTERVAL
done