# 🚀 Professional Deployment Guide

**Best setup for presentations and production: Railway + Vercel**

## 🎯 Why This Setup?

- **Railway (Backend)**: Perfect for FastAPI, always-on, no cold starts, professional performance
- **Vercel (Frontend)**: Lightning-fast Next.js hosting, global CDN, perfect for demos

---

## 📋 **Step 1: Deploy Backend to Railway**

### 1.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (recommended)
3. Verify your account

### 1.2 Deploy Backend
1. **Click "New Project"**
2. **Select "Deploy from GitHub repo"**
3. **Connect your GitHub repository**
4. **Select your repository**
5. **Configure deployment**:
   - **Root Directory**: `api`
   - **Build Command**: Auto-detected (will use requirements.txt)
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

6. **Click "Deploy"**

### 1.3 Get Your Backend URL
- After deployment, Railway will give you a URL like: `https://your-app-production.up.railway.app`
- **Test it**: Visit `https://your-app-production.up.railway.app/docs` to see your API docs

---

## 📋 **Step 2: Deploy Frontend to Vercel**

### 2.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Verify your account

### 2.2 Deploy Frontend
1. **Click "New Project"**
2. **Import your GitHub repository**
3. **Configure the project**:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Install Command**: `npm install`

4. **Set Environment Variable**:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://your-app-production.up.railway.app` (your Railway URL)

5. **Click "Deploy"**

---

## 🧪 **Step 3: Test Your Deployment**

### 3.1 Test Backend
```bash
# Health check
curl https://your-app-production.up.railway.app/health

# API docs
open https://your-app-production.up.railway.app/docs
```

### 3.2 Test Frontend
1. Visit your Vercel URL: `https://your-frontend.vercel.app`
2. Enter test API keys:
   - OpenAI API key (get from platform.openai.com)
   - Google Maps API key (optional)
3. Test single company discovery
4. Verify real-time job tracking works

---

## 🔧 **Quick Commands**

### Local Development
```bash
# Start backend
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables for Local Development
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🎨 **For Your Presentation**

### Demo Flow:
1. **Show the landing page** - Clean, professional UI
2. **Enter API keys** - Explain security (user-provided keys)
3. **Search a well-known company** - e.g., "Microsoft" or "Tesla"
4. **Show real-time progress** - Job status updates live
5. **Display results** - Location data with sources
6. **Show API docs** - Visit `/docs` endpoint

### Key Selling Points:
- ✅ **Secure**: Users provide their own API keys
- ✅ **Scalable**: Serverless frontend, containerized backend
- ✅ **Fast**: No cold starts, global CDN
- ✅ **Professional**: Clean UI, comprehensive API docs
- ✅ **Real-time**: Live job tracking and updates

---

## 🛠️ **Troubleshooting**

### Backend Issues
- **Railway logs**: Check Railway dashboard for build/runtime logs
- **Health check**: Test `/health` endpoint
- **CORS**: Already configured for any frontend origin

### Frontend Issues
- **Environment variables**: Must be set in Vercel dashboard
- **Build errors**: Check Vercel build logs
- **API connection**: Verify backend URL is correct

---

## 📊 **Cost Breakdown**

### Railway (Backend)
- **Free tier**: $5 credit monthly (good for demos)
- **Pro**: $5/month for serious usage
- **Always-on**, no cold starts

### Vercel (Frontend)
- **Free tier**: Perfect for demos and small projects
- **Pro**: $20/month for production apps
- **Global CDN**, instant deployments

**Total cost for demo/testing: FREE** 🎉

---

## 🚀 **Ready to Deploy?**

1. **Railway Backend**: Deploy in ~3 minutes
2. **Vercel Frontend**: Deploy in ~2 minutes
3. **Total setup time**: ~10 minutes
4. **Result**: Professional, fast, scalable app ready for presentation

**Let's do this!** 🎯
