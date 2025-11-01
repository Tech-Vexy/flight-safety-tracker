# Deployment Guide

## Production Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ disk space
- Port 8501 available

### Environment Setup

1. **Clone Repository**
```bash
git clone https://github.com/yourname/flight-safety-tracker.git
cd flight-safety-tracker
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with production settings
```

3. **Production Environment Variables**
```env
# Production database settings
DB_HOST=your-mariadb-host
DB_PORT=3306
DB_NAME=flight_safety_prod
DB_USER=flight_safety_user
DB_PASSWORD=secure_password_here
DB_ROOT_PASSWORD=secure_root_password

# Security settings
DEBUG=False
LOG_LEVEL=WARNING

# Performance tuning
MAX_SEARCH_RESULTS=10
SIMILARITY_THRESHOLD=0.75
```

## Cloud Deployment Options

### Option 1: AWS EC2 + RDS

1. **Launch EC2 Instance**
   - Instance type: t3.medium or larger
   - Security group: Allow ports 80, 443, 8501
   - Install Docker and Docker Compose

2. **Setup RDS MariaDB**
   - Engine: MariaDB 11.2+
   - Instance class: db.t3.micro or larger
   - Enable Vector plugin

3. **Deploy Application**
```bash
# On EC2 instance
git clone https://github.com/yourname/flight-safety-tracker.git
cd flight-safety-tracker

# Configure for RDS
export DB_HOST=your-rds-endpoint.amazonaws.com
export DB_PASSWORD=your-secure-password

# Deploy
docker-compose up -d app
```

### Option 2: Google Cloud Run + Cloud SQL

1. **Setup Cloud SQL**
```bash
gcloud sql instances create flight-safety-db \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=us-central1
```

2. **Build and Deploy**
```bash
# Build container
docker build -t gcr.io/YOUR_PROJECT/flight-safety-tracker .

# Push to registry
docker push gcr.io/YOUR_PROJECT/flight-safety-tracker

# Deploy to Cloud Run
gcloud run deploy flight-safety-tracker \
    --image gcr.io/YOUR_PROJECT/flight-safety-tracker \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DB_HOST=CLOUD_SQL_IP
```

### Option 3: DigitalOcean Droplet

1. **Create Droplet**
   - Image: Docker on Ubuntu 22.04
   - Size: 2GB RAM minimum
   - Add firewall rules for port 8501

2. **Deploy Application**
```bash
# SSH to droplet
ssh root@your-droplet-ip

# Clone and deploy
git clone https://github.com/yourname/flight-safety-tracker.git
cd flight-safety-tracker
./setup.sh setup
```

## Reverse Proxy Setup

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### SSL/HTTPS with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### Docker Logs

```bash
# View application logs
docker-compose logs -f app

# View database logs
docker-compose logs -f mariadb

# View logs with timestamps
docker-compose logs -t app
```

### Health Checks

```bash
# Check application health
curl http://localhost:8501/_stcore/health

# Check database connection
docker-compose exec mariadb mysqladmin ping -h localhost -u root -p
```

### Resource Monitoring

```bash
# Monitor container resources
docker stats

# Check disk usage
df -h
docker system df
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec mariadb mysqldump -u root -p flight_safety > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T mariadb mysqldump -u root -p$DB_ROOT_PASSWORD flight_safety > "backups/backup_$DATE.sql"
gzip "backups/backup_$DATE.sql"

# Keep only last 7 days
find backups/ -name "backup_*.sql.gz" -mtime +7 -delete
```

### Restore from Backup

```bash
# Restore database
gunzip -c backup_20231101_120000.sql.gz | docker-compose exec -T mariadb mysql -u root -p$DB_ROOT_PASSWORD flight_safety
```

## Security Considerations

### Database Security

1. **Change Default Passwords**
   ```env
   DB_PASSWORD=use_strong_password_here
   DB_ROOT_PASSWORD=use_different_strong_password
   ```

2. **Network Security**
   - Use private networks
   - Restrict database access to application only
   - Enable SSL for database connections

3. **Regular Updates**
   ```bash
   # Update base images
   docker-compose pull
   docker-compose up -d
   ```

### Application Security

1. **Environment Variables**
   - Never commit .env files
   - Use secrets management in production
   - Rotate passwords regularly

2. **Network Configuration**
   ```yaml
   # docker-compose.yml
   services:
     mariadb:
       networks:
         - internal
       # Don't expose port 3306 in production
   
   networks:
     internal:
       driver: bridge
       internal: true
   ```

## Performance Tuning

### Database Optimization

```sql
-- MariaDB configuration for production
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL query_cache_size = 268435456; -- 256MB
SET GLOBAL max_connections = 200;
```

### Application Optimization

```python
# Enable caching in production
@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_search(query):
    return search_engine.search(query)
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          memory: 2G
```

## Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```bash
   # Check logs
   docker-compose logs app
   
   # Verify database connection
   docker-compose exec app python -c "from src.database import DatabaseManager; print(DatabaseManager().test_connection())"
   ```

2. **Slow Performance**
   ```bash
   # Check resource usage
   docker stats
   
   # Optimize database
   docker-compose exec mariadb mysql -u root -p -e "OPTIMIZE TABLE incidents;"
   ```

3. **Memory Issues**
   ```yaml
   # Reduce batch sizes in docker-compose.yml
   environment:
     - MAX_SEARCH_RESULTS=3
     - BATCH_SIZE=16
   ```

### Getting Help

- Check application logs: `docker-compose logs app`
- Verify environment variables: `docker-compose config`
- Test database connection: `docker-compose exec mariadb mysql -u app -p`
- Monitor resources: `docker stats`