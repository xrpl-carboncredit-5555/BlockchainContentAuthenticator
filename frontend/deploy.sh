#!/bin/bash

# BCA XRPL Frontend - Cloud Run Deployment Script
# Make sure you have the Google Cloud SDK installed and authenticated

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"glassy-wave-476720-v6"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"bca-xrpl"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting deployment of BCA XRPL Frontend..."
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"


# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ Not authenticated with Google Cloud. Please run 'gcloud auth login'"
    exit 1
fi

# Configure Docker to use gcloud as a credential helper
echo "🔧 Configuring Docker authentication..."
gcloud auth configure-docker gcr.io --quiet

# Set the project
echo "📝 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the Docker image with explicit platform specification for Cloud Run
echo "🏗️ Building Docker image for amd64/linux platform..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

# Tag the image
echo "🏷️ Tagging image..."
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)

# Push to Google Container Registry
echo "📤 Pushing image to Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run with minimal specs for frontend
echo "🚀 Deploying to Cloud Run..."

# Build environment variables string from .env file
echo "📝 Loading environment variables from .env file..."
ENV_VARS_ARG=""
if [ -f .env ]; then
    # Read .env file and convert to Cloud Run env var format
    ENV_VARS=""
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        [[ $line =~ ^#.*$ ]] && continue
        [[ -z $line ]] && continue

        # Add comma if not first variable
        if [ ! -z "$ENV_VARS" ]; then
            ENV_VARS="$ENV_VARS,"
        fi
        ENV_VARS="$ENV_VARS$line"
    done < .env

    if [ -z "$ENV_VARS" ]; then
        echo "⚠️  Warning: .env file exists but no variables were found"
    else
        echo "✅ Environment variables loaded successfully"
        ENV_VARS_ARG="--set-env-vars ${ENV_VARS}"
    fi
else
    echo "⚠️  Warning: .env file not found, deploying without environment variables"
fi

# Deploy with minimal specs optimized for frontend
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

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🎉 BCA XRPL Frontend is now live!"
echo ""
echo "📊 Configuration:"
echo "   Memory: 512Mi"
echo "   CPU: 1"
echo "   Min Instances: 0 (scales to zero when idle)"
echo "   Max Instances: 1"
echo "   Concurrency: 80 requests per instance"
echo ""
echo "🔍 To view logs:"
echo "gcloud logs tail /projects/${PROJECT_ID}/logs/run.googleapis.com%2Frequests --filter=\"resource.labels.service_name=${SERVICE_NAME}\""
echo ""
echo "📝 To update environment variables:"
echo "gcloud run services update ${SERVICE_NAME} --region=${REGION} --set-env-vars KEY=VALUE"
