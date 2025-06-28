# Free Deployment Options for OCR Website

## 1. Railway.app (Recommended)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Deploy with one command
railway login
railway up
```

## 2. Render.com
1. Connect GitHub repo to Render
2. Use these settings:
   - Build Command: `docker build -t ocr-app .`
   - Start Command: `docker run -p 5000:5000 ocr-app`

## 3. Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

## 4. Google Cloud Run (Free Tier)
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/ocr-website

# Deploy to Cloud Run
gcloud run deploy --image gcr.io/PROJECT-ID/ocr-website --platform managed
```

## 5. Heroku (Free alternatives)
Since Heroku removed free tier, try:
- Koyeb.com
- Cyclic.sh
- Deta.sh

## 6. Self-Host with Ngrok
```bash
# Run locally
docker-compose up

# Expose to internet
ngrok http 5000
```

## Quick Deploy Buttons

### Deploy to Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/github)

### Deploy to Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Deploy to Cyclic
[![Deploy to Cyclic](https://deploy.cyclic.app/button.svg)](https://deploy.cyclic.app/)