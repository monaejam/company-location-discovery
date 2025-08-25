# Railway Deployment Guide for Company Location Discovery

## Overview
This guide provides step-by-step instructions for deploying both the FastAPI backend and Next.js frontend on Railway.

## Prerequisites
- Railway account
- GitHub repository connected to Railway
- API keys ready (OpenAI required, Google Maps and Tavily optional)

## Project Structure
```
My-own-project/
├── api/                    # Backend (FastAPI)
│   ├── main.py
│   ├── requirements.txt
│   ├── railway.json
│   ├── nixpacks.toml
│   └── Procfile
└── frontend/              # Frontend (Next.js)
    ├── package.json
    ├── railway.json
    └── nixpacks.toml
```

## Deployment Steps

### 1. Deploy Backend API

1. **Create a new Railway project** for the backend:
   ```bash
   cd api/
   railway login
   railway link
   ```

2. **Set environment variables** in Railway dashboard:
   - No API keys needed in environment (users provide their own)
   - Railway automatically sets `PORT`

3. **Deploy the backend**:
   ```bash
   railway up
   ```

4. **Note your backend URL** (e.g., `https://your-api.up.railway.app`)

### 2. Deploy Frontend

1. **Create another Railway project** for the frontend:
   ```bash
   cd ../frontend/
   railway link
   ```

2. **Set environment variables** in Railway dashboard:
   ```
   NEXT_PUBLIC_API_URL=https://your-api.up.railway.app
   NODE_ENV=production
   ```

3. **Deploy the frontend**:
   ```bash
   railway up
   ```

### 3. Alternative: Monorepo Deployment

If you want to deploy both services from the same repository:

1. **Create railway.json in root**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "services": {
    "api": {
      "root": "/api",
      "build": {
        "builder": "NIXPACKS"
      },
      "deploy": {
        "startCommand": "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
      }
    },
    "frontend": {
      "root": "/frontend",
      "build": {
        "builder": "NIXPACKS"
      },
      "deploy": {
        "startCommand": "npm run start"
      }
    }
  }
}
```

## Fixed Issues

### Backend Port Issue
**Problem**: `Error: Invalid value for '--port': '$PORT' is not a valid integer`

**Solution**: Changed from `$PORT` to `${PORT:-8000}` in:
- `railway.json`
- `Procfile`
- `nixpacks.toml`

### Frontend Build Issue
**Problem**: `npm error signal SIGTERM`

**Solution**: 
- Added proper build commands in `railway.json`
- Created `nixpacks.toml` with Node.js 18
- Set `NODE_ENV=production`

## Environment Variables

### Backend (API)
- `PORT` - Automatically set by Railway
- `PYTHONUNBUFFERED=1` - For proper logging
- `PYTHONDONTWRITEBYTECODE=1` - Optimization

### Frontend
- `NEXT_PUBLIC_API_URL` - Your backend API URL
- `NODE_ENV=production` - Production mode
- `PORT` - Automatically set by Railway

## Verification Steps

1. **Check Backend Health**:
   ```bash
   curl https://your-api.up.railway.app/health
   ```

2. **Check Frontend**:
   - Visit your frontend URL
   - Check browser console for errors
   - Test API connectivity

## Troubleshooting

### CORS Issues
If you see CORS errors:
1. Verify the frontend URL is in the backend's CORS allowed origins
2. Check that `NEXT_PUBLIC_API_URL` is set correctly

### Build Failures
1. Check Railway build logs
2. Ensure all dependencies are in `requirements.txt` (backend) or `package.json` (frontend)
3. Verify Python version (3.11) and Node.js version (18)

### Connection Issues
1. Ensure both services are deployed and running
2. Check that environment variables are set correctly
3. Verify API endpoints are accessible

## Monitoring

### View Logs
```bash
# Backend logs
railway logs -s api

# Frontend logs
railway logs -s frontend
```

### Check Metrics
- Use Railway dashboard to monitor:
  - Memory usage
  - CPU usage
  - Request count
  - Error rates

## Updates and Redeploy

To update your deployment:

1. **Push changes to GitHub**:
   ```bash
   git add .
   git commit -m "Fix deployment issues"
   git push origin main
   ```

2. **Railway auto-deploys** on push to main branch

Or manually trigger:
```bash
railway up
```

## Support

If issues persist:
1. Check Railway build logs for detailed error messages
2. Verify all configuration files are properly formatted
3. Ensure API keys are valid (users provide their own)
4. Contact Railway support with deployment ID

## Success Indicators

✅ Backend returns 200 on `/health` endpoint
✅ Frontend loads without errors
✅ API calls from frontend succeed
✅ Location discovery works with user-provided API keys
✅ No CORS errors in browser console
