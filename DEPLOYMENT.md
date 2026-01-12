# Odoo Multi-Tenant Platform - Deployment Guide

> **Navigation**: [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md) | [AGENT-CONTEXT.md](AGENT-CONTEXT.md)

## Table of Contents

1. [Quick Start (Minimal Configuration)](#quick-start-minimal-configuration)
2. [Docker Compose Best Practices](#docker-compose-best-practices)
3. [Environment-Specific Deployments](#environment-specific-deployments)
4. [Configuration Management](#configuration-management)
5. [Essential Docker Commands](#essential-docker-commands)
6. [Network Configuration](#network-configuration)
7. [Security Best Practices](#security-best-practices)
8. [Performance Optimization](#performance-optimization)
9. [Backup and Recovery](#backup-and-recovery)
10. [VPS Production Deployment](#vps-production-deployment)

---

## Quick Start (Minimal Configuration)

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository
- 4GB+ RAM available for containers

### Step-by-Step Deployment

#### 1. Clone and Setup

```bash
git clone <repository-url> odoo-platform
cd odoo-platform
cp .env.example .env  # Configure environment variables
```

#### 2. Start with Minimal Configuration (Recommended)

The project includes both full production configuration and a proven minimal configuration for quick setup:

```bash
# Quick deployment using minimal configuration (default)
docker-compose up -d

# Check deployment status
docker ps
docker logs odoo_community_18 | grep "HTTP service"
```

#### 3. Verify Installation

```bash
# Test HTTP connectivity (should return HTTP 303 redirect)
curl -I http://localhost:8069

# Expected success indicators:
# ✅ Container shows "HTTP service (werkzeug) running on :8069"
# ✅ curl returns "HTTP/1.1 303 SEE OTHER"
# ✅ Web interface accessible at http://localhost:8069
```

#### 4. Access Odoo Database Manager

1. Open browser: http://localhost:8069
2. You'll see master password generation (this is normal):
   ```
   Warning, your Odoo database manager is not protected.
   To secure it, we have generated the following master password: [generated-password]
   ```
3. **Save this password** - it's required for database operations
4. Create your first database or tenant

#### 5. Configuration Files Used

- **Development**: `configs/odoo/odoo-minimal.conf` (default, proven working)
- **Production**: `configs/odoo/odoo.conf` (full configuration, use after validation)

### Troubleshooting Quick Start

If HTTP server doesn't start:

1. Check logs: `docker logs odoo_community_18`
2. Ensure using minimal configuration (default setup)
3. Verify no port conflicts: `netstat -tlnp | grep 8069`
4. Emergency recovery: `docker-compose down && docker-compose up -d`

### Next Steps

- Create tenant databases via web interface
- Configure business-specific templates
- Set up N8N automation workflows
- Deploy to production VPS (see [VPS Production Deployment](#vps-production-deployment))

---

## Docker Compose Best Practices

### Environment-Specific Deployments

#### Development Environment

```bash
# Use development configuration with debugging features
docker-compose -f docker-compose.yml -f docker-compose.development.yml up -d

# Features enabled:
# - Auto-reload for code changes
# - Debug mode and detailed logging
# - Permissive database filtering
# - Demo data included
# - Read-write volume mounts for development
```

#### Staging Environment

```bash
# Use staging configuration for pre-production testing
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Features:
# - Production-like performance settings (reduced resources)
# - Worker processes enabled for performance testing
# - Security settings active
# - No demo data
# - Basic Traefik routing for staging domain
```

#### Production Environment

```bash
# Use base docker-compose.yml with production configuration
docker-compose up -d

# Automatically uses:
# - configs/odoo/odoo.conf (minimal, proven configuration)
# - Full Traefik labels for multi-tenant routing
# - Optimized resource limits
# - Security headers and SSL configuration
```

---

## Configuration Management

### Switching Configurations

```bash
# Method 1: Use environment-specific docker-compose files (recommended)
docker-compose -f docker-compose.yml -f docker-compose.development.yml up -d

# Method 2: Manual configuration switching
docker-compose down
# Edit docker-compose.yml to change config file path
# - ./configs/odoo/odoo-development.conf:/etc/odoo/odoo.conf:ro
docker-compose up -d
```

### Configuration Validation

```bash
# Before deploying, validate configuration syntax
docker-compose config

# Test with minimal config first (reduces troubleshooting)
# Then gradually switch to more complex configurations

# Verify HTTP server startup
docker logs odoo_community_18 | grep "HTTP service"
```

### Volume Management Best Practices

#### Development Volumes (Read-Write)

```yaml
volumes:
  # Allow real-time code changes
  - ./addons/custom_module:/mnt/extra-addons/custom_module
  - ./configs/odoo/odoo-development.conf:/etc/odoo/odoo.conf:ro
```

#### Production Volumes (Read-Only)

```yaml
volumes:
  # Prevent accidental modifications
  - ./addons/multi_tenant_core:/mnt/extra-addons/multi_tenant_core:ro
  - ./configs/odoo/odoo.conf:/etc/odoo/odoo.conf:ro
```

---

## Essential Docker Commands

### Container Management

```bash
# Start services
docker-compose up -d

# View all containers status
docker-compose ps

# Check resource usage
docker stats

# View logs with timestamps
docker-compose logs -f --timestamps odoo

# Restart specific service
docker-compose restart odoo

# Stop all services
docker-compose down
```

### Debugging and Maintenance

```bash
# Execute commands inside container
docker exec -it odoo_community_18 bash

# Check Odoo process inside container
docker exec odoo_community_18 ps aux

# Database operations
docker exec -it odoo_postgres psql -U odoo -d odoo_master

# Copy files to/from container
docker cp odoo_community_18:/var/lib/odoo/filestore ./backups/

# Inspect container configuration
docker inspect odoo_community_18
```

---

## Network Configuration

### Local Development

```yaml
networks:
  # Override external network for local testing
  monitoring_shared_monitoring_network:
    external: false
    driver: bridge
```

### Production Integration

```yaml
networks:
  # Use shared VPS monitoring network
  monitoring_shared_monitoring_network:
    external: true
    name: monitoring_shared_monitoring_network
```

---

## Security Best Practices

### Secrets Management

```bash
# Use .env file for sensitive data
echo "ODOO_DB_PASSWORD=secure_password" >> .env
echo "ODOO_ADMIN_PASSWORD=admin_secure_password" >> .env

# Never commit passwords to version control
echo ".env" >> .gitignore
```

### Container Security

```yaml
# Run containers as non-root user
services:
  odoo:
    user: odoo  # Default Odoo user

  # Limit container resources
  deploy:
    resources:
      limits:
        cpus: '0.7'
        memory: 1024M
```

---

## Performance Optimization

### Resource Allocation Strategy

- **Development**: Generous resources for debugging (2GB RAM, 1 CPU)
- **Staging**: Production-like but reduced (1.5GB RAM, 0.8 CPU)
- **Production**: Optimized for VPS constraints (1GB RAM, 0.7 CPU)

### Monitoring Container Health

```bash
# Check container resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Monitor container restarts
docker-compose ps

# Check container logs for errors
docker-compose logs --tail=50 odoo | grep -i error
```

---

## Backup and Recovery

### Data Backup

```bash
# Backup PostgreSQL data
docker exec odoo_postgres pg_dumpall -U odoo > backup_all_$(date +%Y%m%d).sql

# Backup Odoo file storage
docker run --rm -v odoo_platform_data:/data -v $(pwd):/backup busybox tar czf /backup/odoo_files_$(date +%Y%m%d).tar.gz /data

# Backup custom addons
tar czf addons_backup_$(date +%Y%m%d).tar.gz ./addons/
```

### Emergency Recovery

```bash
# Complete reset (CAREFUL: destroys all data)
docker-compose down -v
docker system prune -f
docker-compose up -d

# Restore from backup
docker exec -i odoo_postgres psql -U odoo < backup_all_20231201.sql
```

---

## VPS Production Deployment

### Prerequisites

Before deploying on the shared VPS, **MUST READ** these critical infrastructure documents in order:

#### 🚀 IMMEDIATE PRIORITY (Required Reading)

1. **[Core Infrastructure Guide](D:\Programacao\Repositorios\my-portfolio\CLAUDE.md)** - Essential commands, architecture overview, and safety protocols
2. **[File Structure Guide](D:\Programacao\Repositorios\my-portfolio\FILE-STRUCTURE.md)** - Understanding where everything goes and what not to touch
3. **[VPS Compatibility Notes](D:\Programacao\Repositorios\my-portfolio\VPS-COMPATIBILITY-NOTES.md)** - Critical constraints and files you cannot modify

#### 📋 HIGH PRIORITY (Read Before Deployment)

4. **[Script Usage Guide](D:\Programacao\Repositorios\my-portfolio\SCRIPT-USAGE-GUIDE.md)** - How to use management scripts for deployments
5. **[Infrastructure Overview](D:\Programacao\Repositorios\my-portfolio\INFRASTRUCTURE.md)** - Complete architecture understanding for integration
6. **[Security Guidelines](D:\Programacao\Repositorios\my-portfolio\SECURITY.md)** - Security requirements and compliance

#### 🛠️ OPERATIONAL PRIORITY (During Setup)

7. **[Disaster Recovery Plan](D:\Programacao\Repositorios\my-portfolio\DISASTER-RECOVERY-PLAN.md)** - Backup procedures for integration
8. **[Monitoring Configuration](D:\Programacao\Repositorios\my-portfolio\MONITORING-SECURITY-README.md)** - How to configure monitoring for new services

**⚠️ WARNING**: This VPS hosts multiple production services. The first 3 infrastructure files will give you the foundation to safely deploy without breaking existing systems.

### 🔧 VPS Deployment Steps

#### 1. GitHub Repository Setup

```bash
# 1. Push your Odoo project to GitHub
git add .
git commit -m "feat: Add VPS deployment configuration"
git push origin main

# 2. Set up GitHub Container Registry access
# Go to GitHub Settings > Developer Settings > Personal Access Tokens
# Create token with packages:write permissions
```

#### 2. Configure GitHub Secrets

In your GitHub repository, go to Settings > Secrets and Variables > Actions and add:

**Required Secrets:**

```bash
# VPS Access
VPS_HOST=maxhaider.dev  # Your VPS IP/domain
VPS_USER=your_username
VPS_KEY=your_private_ssh_key
VPS_PASSPHRASE=your_key_passphrase  # if applicable

# Container Registry
GHCR_TOKEN=your_github_token  # Token with packages:write permission

# Odoo Configuration
ODOO_DB_PASSWORD=secure_database_password
ODOO_DB_USER=odoo
ODOO_DB_NAME=odoo_master
ODOO_ADMIN_PASSWORD=secure_admin_password

# Email Configuration
EMAIL_HOST=smtp.zoho.com
EMAIL_USER=your_email@domain.com
EMAIL_PASS=your_email_password
EMAIL_FROM=noreply@maxhaider.dev

# Integration APIs (Optional)
N8N_WEBHOOK_URL=https://n8n.maxhaider.dev/webhook/odoo
N8N_API_KEY=your_n8n_api_key
WOOCOMMERCE_API_KEY=your_woocommerce_key
WOOCOMMERCE_API_SECRET=your_woocommerce_secret
GOLD_PRICE_API_KEY=your_gold_price_api_key
```

#### 3. Automatic Deployment

Once secrets are configured, deployment is automatic:

```bash
# 1. Push to main branch triggers production deployment
git push origin main

# 2. GitHub Actions will:
#    - Build Docker image
#    - Push to GitHub Container Registry
#    - Deploy to VPS via SSH
#    - Configure Traefik routing
#    - Start services with health checks
```

#### 4. Manual VPS Deployment (Alternative)

If you prefer manual deployment:

```bash
# 1. SSH to VPS
ssh your_username@maxhaider.dev

# 2. Clone repository
git clone https://github.com/your_username/odoo-platform.git
cd odoo-platform

# 3. Create environment file
cp .env.example .env
# Edit .env with your production configuration

# 4. Ensure monitoring stack is running
docker ps | grep traefik  # Should show Traefik running

# 5. Deploy Odoo
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify deployment
curl -I https://odoo.maxhaider.dev
```

#### 5. DNS Configuration

Configure your domain DNS to point to the VPS:

```bash
# A Records (point to your VPS IP)
odoo.maxhaider.dev -> YOUR_VPS_IP
*.odoo.maxhaider.dev -> YOUR_VPS_IP  # For tenant subdomains

# CNAME Records (if using domain)
odoo.yourdomain.com -> maxhaider.dev
*.odoo.yourdomain.com -> maxhaider.dev
```

#### 6. SSL Certificate Setup

Traefik automatically handles SSL certificates via Let's Encrypt:

```yaml
# Traefik labels in docker-compose.prod.yml handle this automatically
traefik.http.routers.odoo-prod.tls=true
traefik.http.routers.odoo-prod.tls.certresolver=myresolver
```

### 🔍 Deployment Verification

#### Check Services

```bash
# SSH to VPS and verify
ssh your_username@maxhaider.dev
cd ~/odoo-platform

# Check containers
docker ps | grep odoo

# Check logs
docker logs odoo_community_18_prod

# Verify HTTP server
docker logs odoo_community_18_prod | grep "HTTP service"
```

#### Test Endpoints

```bash
# Main platform
curl -I https://odoo.maxhaider.dev

# Database manager
curl -I https://odoo.maxhaider.dev/web/database/manager

# Health check
curl https://odoo.maxhaider.dev/web/health
```

#### Monitor Resources

```bash
# Container resource usage
docker stats

# VPS resource usage
htop

# Check available disk space
df -h
```

### 🔧 Maintenance and Updates

#### Automatic Updates via Watchtower

The deployment includes Watchtower for automatic updates:

```yaml
# Enabled in docker-compose.prod.yml
labels:
  - "com.centurylinklabs.watchtower.enable=true"
```

#### Manual Updates

```bash
# 1. SSH to VPS
ssh your_username@maxhaider.dev
cd ~/odoo-platform

# 2. Pull latest changes
git pull origin main

# 3. Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

#### Backup Procedures

```bash
# Database backup
docker exec odoo_postgres_prod pg_dumpall -U odoo > backup_$(date +%Y%m%d).sql

# File storage backup
docker run --rm -v odoo_data_prod:/data -v $(pwd):/backup busybox tar czf /backup/odoo_files_$(date +%Y%m%d).tar.gz /data

# Configuration backup
tar czf config_backup_$(date +%Y%m%d).tar.gz configs/ .env
```

### 🚨 Troubleshooting VPS Deployment

#### Common Issues

**Deployment Fails:**

```bash
# Check GitHub Actions logs
# Verify all secrets are set correctly
# Ensure VPS has enough resources (4GB+ RAM recommended)
```

**Traefik SSL Issues:**

```bash
# Check Traefik logs
docker logs traefik

# Verify DNS propagation
nslookup odoo.maxhaider.dev

# Check certificate status
curl -vI https://odoo.maxhaider.dev 2>&1 | grep -i certificate
```

**Database Connection Issues:**

```bash
# Check PostgreSQL logs
docker logs odoo_postgres_prod

# Verify database password
docker exec odoo_postgres_prod psql -U odoo -c "SELECT version();"
```

**Memory/Performance Issues:**

```bash
# Check resource limits in docker-compose.prod.yml
# Monitor with: docker stats
# Adjust worker processes in odoo-production.conf
```

---

**Related Documentation**:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and components
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting guide
- [SECURITY.md](SECURITY.md) - Security best practices
- [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) - Tenant management

**Last Updated**: 2026-01-12
