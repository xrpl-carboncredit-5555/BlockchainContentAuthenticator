# Deployment Guide - YouTube XRPL NFT Verifier

**Complete guide for deploying the frontend application to Google Cloud Run**

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Architecture](#deployment-architecture)
4. [Docker Configuration](#docker-configuration)
5. [Google Cloud Run Deployment](#google-cloud-run-deployment)
6. [Deployment Script](#deployment-script)
7. [Environment Configuration](#environment-configuration)
8. [Manual Deployment](#manual-deployment)
9. [Automated Deployment](#automated-deployment)
10. [Post-Deployment](#post-deployment)
11. [Monitoring and Logging](#monitoring-and-logging)
12. [Scaling Configuration](#scaling-configuration)
13. [Cost Optimization](#cost-optimization)
14. [Troubleshooting](#troubleshooting)
15. [CI/CD Integration](#cicd-integration)
16. [Security Best Practices](#security-best-practices)

---

## 1. Overview

The YouTube XRPL NFT Verifier frontend is deployed as a containerized application on **Google Cloud Run**, a fully managed serverless platform for running containers.

### Deployment Strategy

- **Platform**: Google Cloud Run (managed)
- **Container Registry**: Google Container Registry (GCR)
- **Build System**: Docker multi-stage builds
- **Region**: us-central1 (configurable)
- **Scaling**: Automatic with scale-to-zero capability
- **Access**: Public (unauthenticated access allowed)

### Key Benefits

✅ **Serverless**: No server management required
✅ **Scale-to-Zero**: Pay only when traffic exists
✅ **Auto-scaling**: Handles traffic spikes automatically
✅ **Fast Deployments**: Automated deployment script
✅ **Cost-Effective**: Minimal cost for frontend applications
✅ **Global CDN**: Built-in content delivery

---

## 2. Prerequisites

### Required Tools

1. **Google Cloud SDK (gcloud CLI)**
   ```bash
   # Install on macOS
   brew install --cask google-cloud-sdk

   # Install on Linux
   curl https://sdk.cloud.google.com | bash

   # Verify installation
   gcloud --version
   ```

2. **Docker Desktop**
   ```bash
   # Install on macOS
   brew install --cask docker

   # Verify installation
   docker --version
   ```

3. **Git** (for version control)
   ```bash
   git --version
   ```

### Google Cloud Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or use existing
   - Note the Project ID (e.g., `glassy-wave-476720-v6`)

2. **Enable Billing**
   - Link a billing account to your project
   - Required for Cloud Run deployment

3. **Authenticate with gcloud**
   ```bash
   # Login to Google Cloud
   gcloud auth login

   # Verify authentication
   gcloud auth list
   ```

4. **Set Default Project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

### Required Permissions

Your Google Cloud account needs:
- Cloud Run Admin
- Container Registry Service Agent
- Service Account User
- Viewer (for reading project resources)

---

## 3. Deployment Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet Traffic                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Load Balancer                     │
│                  (Automatic HTTPS)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Google Cloud Run                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Docker Container (Next.js App)                │  │
│  │  - Node.js 18 Alpine Runtime                          │  │
│  │  - Next.js 15.5.3 (Standalone Mode)                   │  │
│  │  - Port 3000                                           │  │
│  │  - Memory: 2Gi, CPU: 1                                │  │
│  │  - Auto-scaling: 0-1 instances                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              External Services                              │
│  - XRPL Nodes (wss://xrplcluster.com)                      │
│  - IPFS Gateways (Pinata, ipfs.io, etc.)                   │
└─────────────────────────────────────────────────────────────┘
```

### Container Build Process

```
Source Code (src/)
      ↓
┌──────────────────────────────────────┐
│   Docker Multi-Stage Build          │
│                                      │
│   Stage 1: Dependencies              │
│   - Install node_modules             │
│                                      │
│   Stage 2: Builder                   │
│   - Copy source code                 │
│   - Run next build                   │
│   - Generate standalone output       │
│                                      │
│   Stage 3: Runner (Production)       │
│   - Copy standalone app              │
│   - Copy static assets               │
│   - Set production environment       │
│   - Expose port 3000                 │
└──────────────────────────────────────┘
      ↓
Docker Image (linux/amd64)
      ↓
Google Container Registry (GCR)
      ↓
Google Cloud Run Service
```

---

## 4. Docker Configuration

### Dockerfile Analysis

**Location:** `Dockerfile` (project root)

#### Stage 1: Base Image

```dockerfile
FROM node:18-alpine AS base
```

- **Base OS**: Alpine Linux (lightweight)
- **Node Version**: 18 LTS
- **Size**: ~50MB base image

#### Stage 2: Dependencies Installation

```dockerfile
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN npm ci
```

**Purpose:**
- Install system dependencies
- Install npm packages
- Uses `npm ci` for deterministic builds
- Supports multiple package managers

#### Stage 3: Build Application

```dockerfile
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build
```

**Purpose:**
- Copy dependencies from previous stage
- Copy source code
- Build Next.js application
- Generate standalone output

**Build Output:**
- `.next/standalone/` - Minimal server code
- `.next/static/` - Static assets
- `public/` - Public assets

#### Stage 4: Production Runner

```dockerfile
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
RUN mkdir .next
RUN chown nextjs:nodejs .next

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

**Purpose:**
- Create production runtime
- Security: Non-root user (nextjs)
- Copy only production files
- Set environment variables
- Expose port 3000
- Start Next.js server

### Docker Image Characteristics

| Property | Value |
|----------|-------|
| Base Image | node:18-alpine |
| Final Size | ~150-200MB |
| Build Stages | 4 (multi-stage) |
| Platform | linux/amd64 |
| Runtime User | nextjs (UID 1001) |
| Port | 3000 |
| Entry Point | `node server.js` |

### .dockerignore

**Recommended `.dockerignore` file:**

```
node_modules
.next
.git
.gitignore
README.md
.env
.env.local
.env*.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
*.md
docs/
.claude/
```

**Purpose:** Reduce build context size and exclude unnecessary files

---

## 5. Google Cloud Run Deployment

### Service Configuration

**Default Configuration:**

```yaml
Service Name: bca-xrpl
Region: us-central1
Platform: managed
Access: allow-unauthenticated
Memory: 2Gi
CPU: 1
Min Instances: 0
Max Instances: 1
Timeout: 60 seconds
Concurrency: 80 requests
Port: 3000
```

### Resource Allocation

**Memory: 2Gi**
- Sufficient for Next.js SSR
- Handles IPFS metadata caching
- Room for concurrent requests

**CPU: 1 vCPU**
- Adequate for frontend workload
- Good balance of performance and cost

**Concurrency: 80**
- Up to 80 concurrent requests per instance
- Good for typical frontend traffic

### Scaling Behavior

**Scale-to-Zero (Min Instances: 0)**
- Instance shuts down after ~15 minutes of inactivity
- Saves costs when no traffic
- Cold start: ~2-5 seconds

**Auto-scaling (Max Instances: 1)**
- Single instance deployment
- Suitable for low-to-medium traffic
- Can be increased for higher traffic

**When to Increase Max Instances:**
- Sustained traffic > 80 concurrent users
- Response times degrading
- CPU/Memory utilization consistently high

### Networking

**Public Access:**
- `--allow-unauthenticated` flag
- Publicly accessible URL
- No authentication required

**HTTPS:**
- Automatically provisioned SSL certificate
- Custom domain support available
- HTTP/2 enabled

---

## 6. Deployment Script

### deploy.sh Overview

**Location:** `deploy.sh` (project root)

**Purpose:** Automated deployment to Google Cloud Run

### Script Configuration

#### Environment Variables

```bash
# Configuration (defaults)
PROJECT_ID=${PROJECT_ID:-"glassy-wave-476720-v6"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"bca-xrpl"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
```

**Customization:**
```bash
# Override via environment variables
export PROJECT_ID="my-project-id"
export REGION="us-west1"
export SERVICE_NAME="my-service"
./deploy.sh
```

### Script Workflow

#### Step 1: Pre-flight Checks

```bash
# Check gcloud CLI installation
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE; then
    echo "❌ Not authenticated"
    exit 1
fi
```

#### Step 2: Setup

```bash
# Configure Docker authentication
gcloud auth configure-docker gcr.io --quiet

# Set project
gcloud config set project ${PROJECT_ID}

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Step 3: Build Docker Image

```bash
# Build for linux/amd64 platform (Cloud Run requirement)
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

# Tag with timestamp
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)
```

**Platform Note:** Cloud Run requires linux/amd64 images, even on Apple Silicon Macs

#### Step 4: Push to Registry

```bash
# Push to Google Container Registry
docker push ${IMAGE_NAME}:latest
```

#### Step 5: Load Environment Variables

```bash
# Parse .env file
ENV_VARS=""
while IFS= read -r line; do
    # Skip comments and empty lines
    [[ $line =~ ^#.*$ ]] && continue
    [[ -z $line ]] && continue

    # Build comma-separated list
    if [ ! -z "$ENV_VARS" ]; then
        ENV_VARS="$ENV_VARS,"
    fi
    ENV_VARS="$ENV_VARS$line"
done < .env

ENV_VARS_ARG="--set-env-vars ${ENV_VARS}"
```

**Environment Variables Format:**
```
KEY1=VALUE1,KEY2=VALUE2,KEY3=VALUE3
```

#### Step 6: Deploy to Cloud Run

```bash
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 1 \
    --timeout 60 \
    --concurrency 80 \
    ${ENV_VARS_ARG} \
    --port 3000
```

#### Step 7: Get Service URL

```bash
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --format="value(status.url)")

echo "🌐 Service URL: ${SERVICE_URL}"
```

### Script Output Example

```
🚀 Starting deployment of BCA XRPL Frontend...
Project ID: glassy-wave-476720-v6
Region: us-central1
Service: bca-xrpl

🔧 Configuring Docker authentication...
📝 Setting project to glassy-wave-476720-v6...
🔧 Enabling required APIs...
🏗️ Building Docker image for amd64/linux platform...
🏷️ Tagging image...
📤 Pushing image to Container Registry...
🚀 Deploying to Cloud Run...
📝 Loading environment variables from .env file...
✅ Environment variables loaded successfully

✅ Deployment completed successfully!
🌐 Service URL: https://bca-xrpl-xxxxxxxxxxxx-uc.a.run.app
🎉 BCA XRPL Frontend is now live!

📊 Configuration:
   Memory: 2Gi
   CPU: 1
   Min Instances: 0 (scales to zero when idle)
   Max Instances: 1
   Concurrency: 80 requests per instance
```

---

## 7. Environment Configuration

### .env File Setup

**File:** `.env` (project root, gitignored)

**Required Variables:**

```env
# XRPL Network Configuration
NEXT_PUBLIC_XRPL_NETWORK=mainnet
NEXT_PUBLIC_WALLET_ADDRESS=rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp
```

**Optional Variables:**

```env
# Node Environment (set automatically by Cloud Run)
NODE_ENV=production

# Next.js Configuration
NEXT_TELEMETRY_DISABLED=1
```

### .env.example Template

**File:** `.env.example` (committed to git)

```env
# XRPL Network Configuration
# Options: mainnet | testnet
NEXT_PUBLIC_XRPL_NETWORK=mainnet

# Wallet Address to Query
NEXT_PUBLIC_WALLET_ADDRESS=rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp
```

### Environment Variable Handling

**Local Development:**
- Reads from `.env.local` or `.env`
- Automatically loaded by Next.js

**Cloud Run Deployment:**
- Parsed from `.env` by deploy.sh
- Set via `--set-env-vars` flag
- Available to the Next.js application

**Best Practices:**
1. ✅ Never commit `.env` to git
2. ✅ Keep `.env.example` up to date
3. ✅ Use `NEXT_PUBLIC_` prefix for browser-accessible vars
4. ✅ Validate environment variables in code

---

## 8. Manual Deployment

### Step-by-Step Manual Process

#### 1. Build Docker Image Locally

```bash
# Build for linux/amd64 platform
docker build --platform linux/amd64 -t gcr.io/YOUR_PROJECT_ID/bca-xrpl:latest .

# Test locally (optional)
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_XRPL_NETWORK=mainnet \
  gcr.io/YOUR_PROJECT_ID/bca-xrpl:latest
```

#### 2. Authenticate Docker with GCR

```bash
gcloud auth configure-docker gcr.io
```

#### 3. Push Image to GCR

```bash
docker push gcr.io/YOUR_PROJECT_ID/bca-xrpl:latest
```

#### 4. Deploy to Cloud Run

```bash
gcloud run deploy bca-xrpl \
  --image gcr.io/YOUR_PROJECT_ID/bca-xrpl:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --timeout 60 \
  --concurrency 80 \
  --set-env-vars NEXT_PUBLIC_XRPL_NETWORK=mainnet,NEXT_PUBLIC_WALLET_ADDRESS=rBCA... \
  --port 3000
```

#### 5. Verify Deployment

```bash
# Get service URL
gcloud run services describe bca-xrpl \
  --region us-central1 \
  --format="value(status.url)"

# Test the URL
curl https://your-service-url.run.app
```

---

## 9. Automated Deployment

### Using deploy.sh Script

#### Quick Start

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

#### Custom Configuration

```bash
# Deploy to different project
export PROJECT_ID="my-custom-project"
./deploy.sh

# Deploy to different region
export REGION="us-west1"
./deploy.sh

# Deploy with custom service name
export SERVICE_NAME="my-custom-service"
./deploy.sh

# Combine all
export PROJECT_ID="my-project"
export REGION="europe-west1"
export SERVICE_NAME="xrpl-nft-frontend"
./deploy.sh
```

### Deployment Checklist

Before running `deploy.sh`:

- [ ] `.env` file configured with correct values
- [ ] Google Cloud SDK installed and authenticated
- [ ] Docker Desktop running
- [ ] Project ID confirmed
- [ ] Billing enabled on GCP project
- [ ] Required APIs enabled
- [ ] Sufficient permissions granted

### First-Time Deployment

```bash
# 1. Authenticate with Google Cloud
gcloud auth login

# 2. Set your project
gcloud config set project YOUR_PROJECT_ID

# 3. Create .env file
cp .env.example .env
# Edit .env with your values

# 4. Make deploy script executable
chmod +x deploy.sh

# 5. Run deployment
./deploy.sh
```

**Expected Time:** 5-10 minutes for first deployment

### Subsequent Deployments

```bash
# Simply run the script
./deploy.sh
```

**Expected Time:** 2-5 minutes for subsequent deployments

---

## 10. Post-Deployment

### Verify Deployment

#### 1. Check Service Status

```bash
gcloud run services describe bca-xrpl --region us-central1
```

#### 2. Test Application

```bash
# Get URL
SERVICE_URL=$(gcloud run services describe bca-xrpl \
  --region us-central1 \
  --format="value(status.url)")

# Test homepage
curl $SERVICE_URL

# Test API endpoint
curl $SERVICE_URL/api/videos?address=rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp
```

#### 3. Browser Testing

Visit the service URL in your browser:
- Check homepage loads
- Test NFT verification
- Test video gallery
- Verify IPFS image loading

### Update Environment Variables

```bash
# Update single variable
gcloud run services update bca-xrpl \
  --region us-central1 \
  --set-env-vars NEXT_PUBLIC_XRPL_NETWORK=testnet

# Update multiple variables
gcloud run services update bca-xrpl \
  --region us-central1 \
  --set-env-vars "NEXT_PUBLIC_XRPL_NETWORK=testnet,NEXT_PUBLIC_WALLET_ADDRESS=rNew..."

# Remove variable
gcloud run services update bca-xrpl \
  --region us-central1 \
  --remove-env-vars KEY_NAME
```

### Traffic Management

#### Gradual Rollout

```bash
# Deploy new revision without traffic
gcloud run deploy bca-xrpl \
  --image gcr.io/PROJECT_ID/bca-xrpl:new-version \
  --no-traffic

# Gradually shift traffic
gcloud run services update-traffic bca-xrpl \
  --to-revisions REVISION-001=50,REVISION-002=50

# Full rollout
gcloud run services update-traffic bca-xrpl \
  --to-latest
```

#### Rollback

```bash
# List revisions
gcloud run revisions list --service bca-xrpl

# Rollback to previous revision
gcloud run services update-traffic bca-xrpl \
  --to-revisions PREVIOUS_REVISION=100
```

---

## 11. Monitoring and Logging

### View Logs

#### Real-time Logs

```bash
# Stream all logs
gcloud logs tail /projects/YOUR_PROJECT_ID/logs/run.googleapis.com%2Frequests \
  --filter="resource.labels.service_name=bca-xrpl"

# Stream with timestamps
gcloud logs tail \
  --filter="resource.labels.service_name=bca-xrpl" \
  --format="value(timestamp,textPayload)"
```

#### Historical Logs

```bash
# Last hour
gcloud logs read \
  --filter="resource.labels.service_name=bca-xrpl" \
  --limit 100 \
  --freshness=1h

# Specific time range
gcloud logs read \
  --filter="resource.labels.service_name=bca-xrpl AND timestamp>='2024-01-01T00:00:00Z'" \
  --limit 100
```

#### Error Logs Only

```bash
gcloud logs read \
  --filter="resource.labels.service_name=bca-xrpl AND severity>=ERROR" \
  --limit 50
```

### Cloud Console Monitoring

**Access:** https://console.cloud.google.com/run

**Available Metrics:**
- Request count
- Request latency (p50, p95, p99)
- Container CPU utilization
- Container memory utilization
- Container instance count
- Billable container instance time
- Error rate

### Set Up Alerts

```bash
# Create alert policy (example: high error rate)
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=60s
```

### Application Performance

**Key Metrics to Monitor:**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Response Time (p95) | < 500ms | 500-1000ms | > 1000ms |
| Error Rate | < 1% | 1-5% | > 5% |
| CPU Utilization | < 60% | 60-80% | > 80% |
| Memory Utilization | < 70% | 70-85% | > 85% |
| Cold Start Time | < 2s | 2-5s | > 5s |

---

## 12. Scaling Configuration

### Current Configuration

```
Min Instances: 0
Max Instances: 1
Concurrency: 80
```

### Scaling Scenarios

#### Low Traffic (Default)

```bash
# Scale to zero when idle
--min-instances 0 \
--max-instances 1
```

**Best for:**
- Development/staging
- Low traffic production
- Cost optimization

**Cost:** Pay only when active

#### Medium Traffic

```bash
# Always-warm instance
--min-instances 1 \
--max-instances 3
```

**Best for:**
- Production with consistent traffic
- Avoid cold starts
- Better user experience

**Cost:** ~$10-30/month baseline

#### High Traffic

```bash
# Multiple always-warm instances
--min-instances 2 \
--max-instances 10
```

**Best for:**
- High traffic production
- Critical applications
- SLA requirements

**Cost:** ~$20-100+/month baseline

### Update Scaling

```bash
# Increase max instances
gcloud run services update bca-xrpl \
  --region us-central1 \
  --max-instances 5

# Add minimum instances (avoid cold starts)
gcloud run services update bca-xrpl \
  --region us-central1 \
  --min-instances 1

# Adjust concurrency
gcloud run services update bca-xrpl \
  --region us-central1 \
  --concurrency 100
```

### CPU and Memory Adjustments

```bash
# Increase memory
gcloud run services update bca-xrpl \
  --region us-central1 \
  --memory 4Gi

# Adjust CPU
gcloud run services update bca-xrpl \
  --region us-central1 \
  --cpu 2

# CPU throttling (always allocated)
gcloud run services update bca-xrpl \
  --region us-central1 \
  --cpu-throttling
```

---

## 13. Cost Optimization

### Cloud Run Pricing (as of 2024)

**Free Tier (per month):**
- 2 million requests
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds

**Paid Tier:**
- $0.00002400 per request (after free tier)
- $0.00000250 per GB-second memory
- $0.00002400 per vCPU-second

### Cost Estimates

#### Scenario 1: Low Traffic (Default Config)

```
Traffic: 10,000 requests/month
Avg Response: 200ms
Config: 2Gi RAM, 1 CPU, min=0, max=1

Monthly Cost: ~$0 (within free tier)
```

#### Scenario 2: Medium Traffic

```
Traffic: 100,000 requests/month
Avg Response: 300ms
Config: 2Gi RAM, 1 CPU, min=1, max=3

Monthly Cost: ~$15-25
```

#### Scenario 3: High Traffic

```
Traffic: 1,000,000 requests/month
Avg Response: 400ms
Config: 4Gi RAM, 2 CPU, min=2, max=10

Monthly Cost: ~$75-150
```

### Cost Optimization Tips

1. **Scale to Zero**
   - Set `min-instances=0` for dev/staging
   - Saves ~$10-20/month per service

2. **Right-size Resources**
   - Monitor actual CPU/memory usage
   - Reduce if consistently < 50% utilized

3. **Optimize Response Times**
   - Faster responses = less billable time
   - Implement caching (already done!)

4. **Use Concurrency**
   - Higher concurrency = fewer instances
   - Current: 80 (good balance)

5. **Regional Deployment**
   - Deploy only in required regions
   - Avoid unnecessary multi-region

### Cost Monitoring

```bash
# View current month costs
gcloud billing accounts list
gcloud billing projects describe YOUR_PROJECT_ID

# Set budget alerts
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Monthly Budget" \
  --budget-amount=50USD \
  --threshold-rule=percent=90
```

---

## 14. Troubleshooting

### Common Issues

#### Issue 1: Build Fails on Apple Silicon (M1/M2)

**Error:**
```
exec /usr/local/bin/docker-entrypoint.sh: exec format error
```

**Solution:**
```bash
# Build with explicit platform
docker build --platform linux/amd64 -t image-name .
```

**Explanation:** Cloud Run requires linux/amd64, Apple Silicon is arm64

#### Issue 2: Environment Variables Not Loaded

**Symptoms:** App uses default values instead of .env

**Solutions:**

1. Check .env file exists
   ```bash
   ls -la .env
   ```

2. Verify format (no quotes needed)
   ```env
   # Correct
   NEXT_PUBLIC_XRPL_NETWORK=mainnet

   # Incorrect
   NEXT_PUBLIC_XRPL_NETWORK="mainnet"
   ```

3. Re-deploy with explicit env vars
   ```bash
   gcloud run services update bca-xrpl \
     --set-env-vars "NEXT_PUBLIC_XRPL_NETWORK=mainnet"
   ```

#### Issue 3: Service Unavailable (503)

**Possible Causes:**

1. Container not starting
   ```bash
   # Check logs for errors
   gcloud logs read --filter="resource.labels.service_name=bca-xrpl" --limit 50
   ```

2. Port mismatch
   ```bash
   # Verify port is 3000
   gcloud run services describe bca-xrpl --format="value(spec.template.spec.containers.ports.containerPort)"
   ```

3. Health check failing
   ```bash
   # Test locally
   docker run -p 3000:3000 gcr.io/PROJECT_ID/bca-xrpl:latest
   curl localhost:3000
   ```

#### Issue 4: Slow Cold Starts

**Symptoms:** First request after idle takes > 5 seconds

**Solutions:**

1. Add minimum instances
   ```bash
   gcloud run services update bca-xrpl --min-instances 1
   ```

2. Optimize image size
   - Review dependencies
   - Remove unused packages
   - Use multi-stage builds (already implemented)

3. Implement health check endpoint
   - Keeps container warm
   - Faster startup

#### Issue 5: Out of Memory

**Error in logs:**
```
Container exceeded memory limit
```

**Solutions:**

1. Increase memory
   ```bash
   gcloud run services update bca-xrpl --memory 4Gi
   ```

2. Check for memory leaks
   - Review cache sizes
   - Monitor memory usage

3. Implement better caching limits
   - Already implemented in ipfsCache.ts
   - Verify limits are appropriate

### Debug Commands

```bash
# Get service details
gcloud run services describe bca-xrpl --region us-central1

# List all revisions
gcloud run revisions list --service bca-xrpl --region us-central1

# Get revision details
gcloud run revisions describe REVISION_NAME --region us-central1

# Test locally with same config
docker run -p 3000:3000 \
  -e NODE_ENV=production \
  -e NEXT_PUBLIC_XRPL_NETWORK=mainnet \
  gcr.io/PROJECT_ID/bca-xrpl:latest

# Check container logs locally
docker logs CONTAINER_ID
```

---

## 15. CI/CD Integration

### GitHub Actions Example

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

env:
  PROJECT_ID: glassy-wave-476720-v6
  SERVICE_NAME: bca-xrpl
  REGION: us-central1

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ env.PROJECT_ID }}

      - name: Configure Docker
        run: gcloud auth configure-docker gcr.io

      - name: Build Docker image
        run: |
          docker build --platform linux/amd64 \
            -t gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }} \
            -t gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:latest \
            .

      - name: Push to GCR
        run: |
          docker push gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }}
          docker push gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:latest

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --image gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }} \
            --region ${{ env.REGION }} \
            --platform managed \
            --allow-unauthenticated \
            --memory 2Gi \
            --cpu 1 \
            --min-instances 0 \
            --max-instances 1 \
            --set-env-vars "NEXT_PUBLIC_XRPL_NETWORK=${{ secrets.XRPL_NETWORK }},NEXT_PUBLIC_WALLET_ADDRESS=${{ secrets.WALLET_ADDRESS }}"
```

### GitLab CI Example

**File:** `.gitlab-ci.yml`

```yaml
variables:
  PROJECT_ID: glassy-wave-476720-v6
  SERVICE_NAME: bca-xrpl
  REGION: us-central1
  IMAGE: gcr.io/$PROJECT_ID/$SERVICE_NAME

stages:
  - build
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - echo $GCP_SA_KEY | docker login -u _json_key --password-stdin https://gcr.io
  script:
    - docker build --platform linux/amd64 -t $IMAGE:$CI_COMMIT_SHA -t $IMAGE:latest .
    - docker push $IMAGE:$CI_COMMIT_SHA
    - docker push $IMAGE:latest

deploy:
  stage: deploy
  image: google/cloud-sdk:alpine
  before_script:
    - echo $GCP_SA_KEY > key.json
    - gcloud auth activate-service-account --key-file=key.json
    - gcloud config set project $PROJECT_ID
  script:
    - |
      gcloud run deploy $SERVICE_NAME \
        --image $IMAGE:$CI_COMMIT_SHA \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 1 \
        --set-env-vars "NEXT_PUBLIC_XRPL_NETWORK=$XRPL_NETWORK,NEXT_PUBLIC_WALLET_ADDRESS=$WALLET_ADDRESS"
  only:
    - main
```

### Required Secrets

For CI/CD, set these secrets in your repository:

- `GCP_SA_KEY`: Service account JSON key
- `XRPL_NETWORK`: Network (mainnet/testnet)
- `WALLET_ADDRESS`: Default wallet address

---

## 16. Security Best Practices

### Container Security

1. **Non-root User**
   ```dockerfile
   # Already implemented
   USER nextjs
   ```

2. **Minimal Base Image**
   - Using Alpine Linux (~50MB vs ~900MB for standard Node)
   - Fewer attack surfaces

3. **No Secrets in Image**
   - Environment variables via Cloud Run
   - Never hardcode secrets

### Cloud Run Security

1. **IAM Permissions**
   ```bash
   # Restrict who can deploy
   gcloud run services add-iam-policy-binding bca-xrpl \
     --member='user:developer@example.com' \
     --role='roles/run.developer'
   ```

2. **Service Account**
   ```bash
   # Use custom service account with minimal permissions
   gcloud run services update bca-xrpl \
     --service-account=custom-sa@project.iam.gserviceaccount.com
   ```

3. **VPC Connector** (if needed)
   ```bash
   # Connect to private resources
   gcloud run services update bca-xrpl \
     --vpc-connector=CONNECTOR_NAME
   ```

### Environment Variables Security

1. **Use Secret Manager** (recommended for sensitive data)
   ```bash
   # Store secret
   echo "secret-value" | gcloud secrets create SECRET_NAME --data-file=-

   # Use in Cloud Run
   gcloud run services update bca-xrpl \
     --update-secrets=ENV_VAR_NAME=SECRET_NAME:latest
   ```

2. **Audit Environment Variables**
   ```bash
   # List all env vars
   gcloud run services describe bca-xrpl \
     --format="value(spec.template.spec.containers.env)"
   ```

### Network Security

1. **Enable Cloud Armor** (DDoS protection)
2. **Use Cloud CDN** for static assets
3. **Implement rate limiting** in application code
4. **Monitor for suspicious traffic**

### Regular Maintenance

- [ ] Update base image regularly
- [ ] Scan for vulnerabilities
- [ ] Review IAM permissions quarterly
- [ ] Rotate secrets/credentials
- [ ] Monitor security advisories

---

## Appendix A: Quick Reference

### Common Commands

```bash
# Deploy
./deploy.sh

# Update env vars
gcloud run services update bca-xrpl --set-env-vars KEY=VALUE

# View logs
gcloud logs tail --filter="resource.labels.service_name=bca-xrpl"

# Scale up
gcloud run services update bca-xrpl --max-instances 5

# Rollback
gcloud run services update-traffic bca-xrpl --to-revisions REV=100

# Delete service
gcloud run services delete bca-xrpl --region us-central1
```

### Configuration Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Container build configuration |
| `deploy.sh` | Automated deployment script |
| `.env` | Environment variables |
| `next.config.ts` | Next.js configuration |
| `package.json` | Dependencies and scripts |

### Useful Links

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Container Registry](https://cloud.google.com/container-registry/docs)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference/run)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)

---

**Document Version:** 1.0
**Last Updated:** November 14, 2025
**Maintained By:** Development Team
