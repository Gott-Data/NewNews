# NewNews Vercel Deployment Guide

## Overview

DeepTutorNews has two components that need separate deployments:
- **Frontend (Next.js)**: Deploy to Vercel
- **Backend (FastAPI)**: Deploy to a Python hosting service

## Option 1: Frontend on Vercel + Backend on Railway/Render

### Step 1: Deploy Backend (Choose one)

#### Option A: Railway (Recommended)

1. Go to [Railway.app](https://railway.app/)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `NewNews` repository
4. Add environment variables:
   ```
   LLM_BINDING_API_KEY=your_openai_key
   NEWSAPI_KEY=your_newsapi_key
   GUARDIAN_API_KEY=your_guardian_key
   STABILITY_API_KEY=your_stability_key
   PERPLEXITY_API_KEY=your_perplexity_key
   PORT=8001
   ```
5. Railway will auto-detect Python and deploy
6. Copy your Railway backend URL (e.g., `https://your-app.railway.app`)

#### Option B: Render.com

1. Go to [Render.com](https://render.com/)
2. Click "New +" → "Web Service"
3. Connect your `NewNews` repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt && pip install -r requirements_news.txt`
   - **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as above)
6. Deploy and copy your Render URL

#### Option C: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Set secrets
fly secrets set LLM_BINDING_API_KEY=your_key
fly secrets set NEWSAPI_KEY=your_key
fly secrets set GUARDIAN_API_KEY=your_key
fly secrets set STABILITY_API_KEY=your_key
fly secrets set PERPLEXITY_API_KEY=your_key

# Deploy
fly deploy
```

### Step 2: Deploy Frontend to Vercel

#### Method A: Using Vercel Dashboard (Easiest)

1. Go to [vercel.com](https://vercel.com/)
2. Click "Add New..." → "Project"
3. Import your `NewNews` repository from GitHub
4. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = Your backend URL from Step 1
6. Click "Deploy"

#### Method B: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from the web directory
cd web
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? newnews
# - Directory? ./
# - Override settings? No

# Add environment variable
vercel env add NEXT_PUBLIC_API_URL

# Paste your backend URL when prompted

# Deploy to production
vercel --prod
```

### Step 3: Update API Proxy in vercel.json

Update the `vercel.json` in the root directory:

```json
{
  "buildCommand": "cd web && npm install && npm run build",
  "outputDirectory": "web/.next",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend-url.railway.app/api/:path*"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://your-backend-url.railway.app"
  }
}
```

Replace `your-backend-url.railway.app` with your actual backend URL.

## Option 2: All-in-One Vercel Deployment (Advanced)

If you want to deploy both frontend and backend to Vercel, you need to convert the FastAPI backend to serverless functions.

### Step 1: Create Vercel Serverless API

Create `api/index.py` in the root:

```python
from src.api.main import app

# Vercel serverless handler
def handler(request):
    return app(request.scope, request.receive, request.send)
```

### Step 2: Update vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "web/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "web/$1"
    }
  ]
}
```

### Step 3: Create requirements.txt in api folder

```bash
cp requirements.txt api/requirements.txt
cp requirements_news.txt api/requirements_news.txt
```

**Note**: Vercel serverless functions have limitations:
- 50MB deployment size limit
- 10-second execution timeout (Pro: 60s, Enterprise: 900s)
- Stateless execution (file storage won't persist)

This might not work well for the news aggregation features.

## Recommended Architecture

**Best Setup**:
- ✅ **Frontend**: Vercel (free tier, excellent Next.js support)
- ✅ **Backend**: Railway or Render (free tier available, better for Python)
- ✅ **Storage**: Use cloud storage (S3, Cloudflare R2) instead of local files

## Environment Variables Summary

### Backend (.env)
```bash
LLM_BINDING_API_KEY=sk-...
NEWSAPI_KEY=...
GUARDIAN_API_KEY=...
STABILITY_API_KEY=...
PERPLEXITY_API_KEY=...
PORT=8001
```

### Frontend (Vercel Dashboard)
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## Post-Deployment Checklist

- [ ] Backend is accessible at your URL
- [ ] Test API: `curl https://your-backend.com/health`
- [ ] Frontend can reach backend API
- [ ] Environment variables are set correctly
- [ ] News aggregation works: `POST /api/v1/news/fetch`
- [ ] Fact-checking works: `POST /api/v1/fact_check/verify`
- [ ] Trend analysis works: `GET /api/v1/trends/trending`
- [ ] Image generation works: `POST /api/v1/content/generate/image`

## Troubleshooting

### Frontend can't reach backend
- Check CORS settings in backend `main.py`
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check browser console for errors

### Backend deployment fails
- Ensure all dependencies are in requirements files
- Check Python version compatibility (3.11+)
- Verify environment variables are set

### Serverless timeout errors
- Use Railway/Render instead of Vercel serverless for backend
- Increase timeout limits (Pro/Enterprise Vercel)
- Optimize long-running operations

## Cost Estimates

### Free Tier Options:
- **Vercel**: Free (Frontend)
- **Railway**: $5/month credit (Backend)
- **Render**: Free tier available (Backend)
- **Fly.io**: $5/month credit (Backend)

### Estimated Monthly Cost:
- Hobby/Personal: **$0-10/month**
- Production: **$20-50/month**

## Support

For deployment issues:
- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs

Good luck with your deployment! 🚀
