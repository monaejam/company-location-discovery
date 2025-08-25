#!/bin/bash

echo "🚀 Railway Deployment Helper Script"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "api/main.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

echo ""
echo "📋 Pre-deployment Checklist:"
echo "----------------------------"
echo "1. Ensure you're logged into Railway CLI: railway login"
echo "2. Have two Railway services created (frontend and backend)"
echo "3. Set environment variables in Railway dashboard:"
echo "   - Frontend: NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app"
echo ""

read -p "Have you completed the checklist? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please complete the checklist first."
    exit 1
fi

echo ""
echo "🔧 Option 1: Deploy with Dockerfiles (Recommended)"
echo "---------------------------------------------------"
echo "This uses the Dockerfiles which have explicit PORT handling"
echo ""
echo "For Backend API:"
echo "  cd api/"
echo "  railway link  # Link to your backend service"
echo "  railway up --dockerfile Dockerfile"
echo ""
echo "For Frontend:"
echo "  cd ../frontend/"
echo "  railway link  # Link to your frontend service"
echo "  railway up --dockerfile Dockerfile"
echo ""

echo "🔧 Option 2: Deploy with simplified configs"
echo "-------------------------------------------"
echo "This uses the railway.json configs with simple_start.py"
echo ""
echo "  git add ."
echo "  git commit -m 'Fix Railway deployment'"
echo "  git push origin main"
echo ""
echo "Railway will auto-deploy from GitHub"
echo ""

echo "🔧 Option 3: Manual deployment commands"
echo "---------------------------------------"
echo "Backend:"
echo "  cd api/"
echo "  railway link"
echo "  railway variables set PYTHONUNBUFFERED=1"
echo "  railway up"
echo ""
echo "Frontend:"
echo "  cd ../frontend/"
echo "  railway link"
echo "  railway variables set NODE_ENV=production"
echo "  railway variables set NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app"
echo "  railway up"
echo ""

echo "📝 Troubleshooting:"
echo "------------------"
echo "If deployment fails, check:"
echo "1. Railway build logs: railway logs"
echo "2. Ensure PORT is not hardcoded anywhere"
echo "3. Check memory usage (may need to upgrade plan)"
echo "4. Verify all dependencies are installable"
echo ""
echo "For the safest deployment, use Option 1 with Dockerfiles!"
