# Internal Back Office - Deployment Guide

## Overview

This guide covers deploying the Internal Back Office application to production environments.

## Pre-Deployment Checklist

- [ ] Update `.env.production` with production values
- [ ] Set strong `NEXTAUTH_SECRET`
- [ ] Configure real backend API URL
- [ ] Set up SSO (Google Workspace or Okta)
- [ ] Review security settings
- [ ] Run type checks: `npm run type-check`
- [ ] Build locally: `npm run build`
- [ ] Test build: `npm run start`

## Environment Configuration

### Production Environment Variables

Create a `.env.production` file with:

```env
# App Configuration
NEXT_PUBLIC_APP_NAME=Backoffice Admin
NEXT_PUBLIC_APP_URL=https://admin.example.com
NEXT_PUBLIC_MOCK_MODE=false
NEXT_PUBLIC_MOCK_AUTH=false

# API Configuration
NEXT_PUBLIC_API_URL=https://api.example.com

# SSO Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OKTA_DOMAIN=your-okta-domain.okta.com
OKTA_CLIENT_ID=your-okta-client-id

# Session & Security
NEXTAUTH_SECRET=generate-long-random-string-at-least-32-chars
NEXTAUTH_URL=https://admin.example.com
SESSION_MAX_AGE=86400  # 24 hours

# Analytics (Optional)
NEXT_PUBLIC_GA_ID=your-google-analytics-id
SENTRY_DSN=your-sentry-dsn

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=900000  # 15 minutes in ms
```

### Generate NEXTAUTH_SECRET

```bash
# Generate a secure random string
openssl rand -base64 32
```

## Deployment Platforms

### Option 1: Vercel (Recommended)

Vercel is the official Next.js deployment platform.

#### Setup Steps

1. **Push code to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to https://vercel.com
   - Click "New Project"
   - Select your GitHub repository
   - Click "Import"

3. **Configure Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add all production environment variables
   - Click "Save"

4. **Deploy**
   - Vercel automatically deploys on push to `main`
   - Preview deployments for pull requests
   - View deployment at provided URL

5. **Custom Domain**
   - Go to Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

#### Benefits
- Zero configuration deployment
- Automatic SSL/TLS certificates
- Built-in CDN
- Analytics and monitoring
- Preview deployments
- Automatic scaling

### Option 2: AWS (EC2 + Load Balancer)

For self-managed infrastructure.

#### Setup Steps

1. **Build Application**
   ```bash
   npm run build
   ```

2. **Create Docker Image**
   ```dockerfile
   FROM node:18-alpine

   WORKDIR /app

   # Install dependencies
   COPY package*.json ./
   RUN npm ci --only=production

   # Copy built application
   COPY .next .next
   COPY public public

   EXPOSE 3000

   CMD ["npm", "start"]
   ```

3. **Build Docker Image**
   ```bash
   docker build -t backoffice:latest .
   ```

4. **Push to ECR**
   ```bash
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-west-2.amazonaws.com
   docker tag backoffice:latest 123456789.dkr.ecr.us-west-2.amazonaws.com/backoffice:latest
   docker push 123456789.dkr.ecr.us-west-2.amazonaws.com/backoffice:latest
   ```

5. **Deploy to ECS**
   - Create ECS cluster
   - Create task definition
   - Create service
   - Configure load balancer

### Option 3: Google Cloud Run

For serverless deployment.

#### Setup Steps

1. **Create Docker Image** (same as AWS)

2. **Push to Google Container Registry**
   ```bash
   docker tag backoffice:latest gcr.io/PROJECT_ID/backoffice:latest
   docker push gcr.io/PROJECT_ID/backoffice:latest
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy backoffice \
     --image gcr.io/PROJECT_ID/backoffice:latest \
     --platform managed \
     --region us-central1 \
     --set-env-vars NEXTAUTH_SECRET=your-secret,NEXT_PUBLIC_API_URL=https://api.example.com
   ```

### Option 4: Azure App Service

For Azure cloud deployment.

#### Setup Steps

1. **Build Application**
   ```bash
   npm run build
   ```

2. **Create Azure App Service**
   - Go to Azure Portal
   - Create "App Service"
   - Select Node.js runtime
   - Configure settings

3. **Deploy**
   ```bash
   az webapp deployment source config-zip --resource-group myGroup --name myApp --src app.zip
   ```

## SSL/TLS Certificate Setup

### Vercel
- Automatic SSL with Let's Encrypt

### AWS
- Use AWS Certificate Manager (ACM)
- Free certificates for AWS resources

### Manual (All Platforms)
- Use Let's Encrypt: `certbot certonly`
- Configure in reverse proxy (nginx)

## Reverse Proxy Configuration

### Nginx Example

```nginx
upstream nextjs {
  server localhost:3000;
}

server {
  listen 80;
  server_name admin.example.com;
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  server_name admin.example.com;

  ssl_certificate /etc/letsencrypt/live/admin.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/admin.example.com/privkey.pem;

  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;

  location / {
    proxy_pass http://nextjs;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  # Static files with caching
  location /_next/static {
    proxy_pass http://nextjs;
    expires 30d;
    add_header Cache-Control "public, immutable";
  }
}
```

### Apache Example

```apache
<VirtualHost *:443>
  ServerName admin.example.com

  SSLEngine on
  SSLCertificateFile /etc/letsencrypt/live/admin.example.com/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/admin.example.com/privkey.pem

  ProxyPreserveHost On
  ProxyPass / http://localhost:3000/
  ProxyPassReverse / http://localhost:3000/

  # Enable WebSocket support
  RewriteEngine On
  RewriteCond %{HTTP:Upgrade} websocket [NC]
  RewriteCond %{HTTP:Connection} upgrade [NC]
  RewriteRule ^/?(.*) "http://localhost:3000/$1" [P,L]
</VirtualHost>

<VirtualHost *:80>
  ServerName admin.example.com
  Redirect permanent / https://admin.example.com/
</VirtualHost>
```

## Performance Optimization

### Production Build

```bash
npm run build
npm start
```

The production build:
- Minifies JavaScript and CSS
- Optimizes images
- Code splits for faster loading
- Enables server-side rendering optimization

### CDN Setup

Recommended CDN providers:
- **Vercel**: Integrated (Edge Network)
- **Cloudflare**: Works with any origin
- **AWS CloudFront**: AWS-native solution
- **Fastly**: High-performance option

#### Cloudflare Configuration

1. Add your domain to Cloudflare
2. Update nameservers at registrar
3. Configure caching rules:
   ```
   Cache Everything: *.example.com/_next/*
   Browser Cache TTL: 30 days
   ```

### Image Optimization

The app uses Next.js Image optimization:
- Automatic WebP conversion
- Responsive image sizes
- Lazy loading

## Monitoring & Logging

### Application Monitoring

Integrate with monitoring services:

```typescript
// lib/monitoring.ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});
```

Services to consider:
- **Sentry**: Error tracking and performance monitoring
- **DataDog**: Full-stack monitoring
- **New Relic**: Application performance monitoring
- **LogRocket**: Frontend monitoring and replay

### Health Checks

Add health check endpoint:

```typescript
// pages/api/health.ts
export default function handler(req, res) {
  res.status(200).json({ status: 'ok', timestamp: new Date() });
}
```

Monitor with:
- Uptime Robot
- Pingdom
- AWS CloudWatch
- Google Cloud Monitoring

### Log Aggregation

Services:
- **ELK Stack**: Open-source solution
- **Datadog**: Enterprise solution
- **CloudWatch**: AWS-native
- **Stackdriver**: GCP-native

## Security Hardening

### Headers

Add security headers via `next.config.js`:

```javascript
async headers() {
  return [
    {
      source: '/:path*',
      headers: [
        {
          key: 'X-Content-Type-Options',
          value: 'nosniff'
        },
        {
          key: 'X-Frame-Options',
          value: 'DENY'
        },
        {
          key: 'X-XSS-Protection',
          value: '1; mode=block'
        },
        {
          key: 'Strict-Transport-Security',
          value: 'max-age=31536000; includeSubDomains'
        },
        {
          key: 'Content-Security-Policy',
          value: "default-src 'self'; script-src 'self' 'unsafe-inline'"
        }
      ]
    }
  ]
}
```

### Rate Limiting

Add rate limiting middleware:

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Add rate limiting logic
  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
};
```

## Backup & Disaster Recovery

### Database Backups
- Daily automated backups
- 30-day retention
- Test restore procedures monthly

### Application Rollback
- Keep previous builds available
- Use blue-green deployment
- Rapid rollback capability

### Disaster Recovery Plan
1. Backup verification (weekly)
2. Failover testing (monthly)
3. Recovery time objective (RTO): < 1 hour
4. Recovery point objective (RPO): < 15 minutes

## Maintenance

### Regular Updates

```bash
# Check for updates
npm outdated

# Update packages
npm update

# Major version updates (test thoroughly)
npm install package@latest
```

### Performance Monitoring

Check regularly:
- Page load times
- API response times
- Error rates
- Database query performance

### Log Rotation

Configure log rotation:

```bash
# /etc/logrotate.d/backoffice
/var/log/backoffice/*.log {
  daily
  rotate 14
  compress
  delaycompress
  notifempty
  create 0640 www-data www-data
  sharedscripts
  postrotate
    systemctl reload nginx
  endscript
}
```

## Troubleshooting Deployment

### Build Fails
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

### Out of Memory
- Increase Node.js heap size
- Optimize dependencies
- Use production mode

### High Latency
- Check CDN configuration
- Verify database connection
- Review middleware performance

## Performance Benchmarks

Target metrics for production:

| Metric | Target |
|--------|--------|
| FCP | < 1.5s |
| LCP | < 2.5s |
| CLS | < 0.1 |
| TTI | < 3s |
| Server Response | < 200ms |
| 95th Percentile Latency | < 1s |

## Cost Optimization

### Vercel
- Free tier available
- Pro: $20/month
- Enterprise: Custom pricing

### AWS
- Use Reserved Instances for stable load
- CloudFront for content delivery
- RDS for managed database

### GCP
- Always Free tier available
- Cloud Run pay-per-use
- Cloud Storage for backup

## Compliance & Security

- Enable audit logging
- Implement MFA for admin accounts
- Regular security audits
- GDPR/CCPA compliance checks
- Data encryption in transit and at rest
- Regular penetration testing

## Support & Escalation

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test API connectivity
4. Check system resources
5. Review monitoring dashboards

## Rollback Procedures

If deployment fails:

```bash
# Revert to previous version
git revert HEAD
git push origin main

# Vercel automatically redeploys
# Or manually trigger deployment
```

For immediate rollback:
- Use blue-green deployment
- Keep previous build available
- Fast rollback capability

---

**Need Help?** Contact DevOps team or check monitoring dashboards for detailed error logs.
