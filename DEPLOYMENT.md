# Deployment Guide

## 🚀 Step-by-Step Deployment to Vercel

### 1. Prepare Your Repository

Make sure your code is committed to GitHub:

```bash
git add .
git commit -m "Clean up project and prepare for deployment"
git push origin main
```

### 2. Deploy Backend (FastAPI)

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**
2. **Click "New Project"**
3. **Import your GitHub repository**
4. **Configure the backend**:
   - **Framework Preset**: Other
   - **Root Directory**: `api`
   - **Build Command**: Leave empty (not needed for Python)
   - **Output Directory**: Leave empty
   - **Install Command**: `pip install -r requirements.txt`

5. **Click "Deploy"**
6. **Wait for deployment** - you'll get a URL like: `https://your-backend-abc123.vercel.app`

### 3. Test Backend

Visit your backend URL and add `/docs` to see the API documentation:
- Example: `https://your-backend-abc123.vercel.app/docs`
- Health check: `https://your-backend-abc123.vercel.app/health`

### 4. Deploy Frontend (Next.js)

1. **Create another Vercel project** for the frontend
2. **Import the same GitHub repository**
3. **Configure the frontend**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: Leave empty (Next.js default)
   - **Install Command**: `npm install`

4. **Set Environment Variables**:
   - Go to **Settings** → **Environment Variables**
   - Add: `NEXT_PUBLIC_API_URL` = `https://your-backend-abc123.vercel.app`
   - Make sure to use your actual backend URL

5. **Click "Deploy"**

### 5. Test Complete System

1. **Visit your frontend URL**: `https://your-frontend-xyz789.vercel.app`
2. **Enter API keys** (get your own from the providers)
3. **Test single company discovery**
4. **Check that jobs are created and tracked properly**

## 🔧 Environment Variables

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=https://your-backend-abc123.vercel.app
```

### Backend

No environment variables needed - users provide their own API keys!

## 🛠️ Local Development

### Start Backend
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Setup for Local Development

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🔍 Troubleshooting

### Backend Issues

1. **Deployment fails**:
   - Check that `requirements.txt` is in the `api/` directory
   - Ensure Python version compatibility
   - Check Vercel build logs

2. **CORS errors**:
   - Verify CORS middleware is configured
   - Check that frontend URL is correct

3. **API not responding**:
   - Check `/health` endpoint
   - Review Vercel function logs

### Frontend Issues

1. **Build fails**:
   - Check Node.js version (should be 18+)
   - Verify all dependencies are installed
   - Check for TypeScript errors

2. **API calls fail**:
   - Verify `NEXT_PUBLIC_API_URL` is set correctly
   - Check browser console for CORS errors
   - Test backend URL directly

3. **Environment variables not working**:
   - Environment variables must start with `NEXT_PUBLIC_` for client-side access
   - Redeploy after adding environment variables

## 📝 Deployment Checklist

### Pre-deployment
- [ ] Code is committed and pushed to GitHub
- [ ] All unnecessary files are removed
- [ ] Requirements files are up to date
- [ ] Local testing is complete

### Backend Deployment
- [ ] Vercel project created
- [ ] Root directory set to `api`
- [ ] Deployment successful
- [ ] Health check endpoint works
- [ ] API docs accessible

### Frontend Deployment
- [ ] Vercel project created
- [ ] Root directory set to `frontend`
- [ ] Environment variable `NEXT_PUBLIC_API_URL` set
- [ ] Deployment successful
- [ ] Frontend loads correctly
- [ ] API calls work

### Final Testing
- [ ] End-to-end functionality works
- [ ] Job creation and tracking works
- [ ] Error handling works properly
- [ ] Mobile responsiveness verified

## 🔗 Useful Links

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

## 🆘 Getting Help

If you encounter issues:

1. Check Vercel deployment logs
2. Test endpoints individually
3. Verify environment variables
4. Check browser console for errors
5. Review API documentation at `/docs` endpoint
