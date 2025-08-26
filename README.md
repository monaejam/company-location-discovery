# Company Location Discovery System

🌍 AI-powered multi-agent system for discovering company locations worldwide using FastAPI backend and Next.js frontend.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) - Containerized deployment
- **Frontend**: Next.js (TypeScript/React) - Static site generation
- **API Keys**: User-provided (no server-side storage)
- **Database**: In-memory storage (jobs are temporary)

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- Python 3.8+
- Your own API keys:
  - OpenAI API key (required)
  - Google Maps API key (optional, recommended)
  - Tavily API key (optional)

### 1. Backend Setup (FastAPI)

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 2. Frontend Setup (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## 🌐 Deployment

### Railway Deployment (Recommended)

This project is optimized for Railway deployment with automatic Docker builds and seamless scaling.

#### Deploy Backend to Railway

1. **Create Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Connect Repository**: Link your GitHub repository
3. **Deploy Backend**:
   ```bash
   cd api
   railway login
   railway init
   railway up
   ```
4. **Configure**: Railway automatically detects the Dockerfile and builds
5. **Get URL**: Railway provides your backend URL (e.g., `https://your-app.up.railway.app`)

#### Deploy Frontend to Railway

1. **Deploy Frontend**:
   ```bash
   cd frontend
   railway init
   railway up
   ```
2. **Set Environment Variables** in Railway dashboard:
   - `NEXT_PUBLIC_API_URL`: Your backend Railway URL
   - `NODE_ENV`: `production`

#### Alternative: Monorepo Deployment

Deploy both services from root directory using the included `railway.json` configuration:
```bash
railway init
railway up
```

### Other Deployment Options

- **Local/VPS**: Direct deployment with uvicorn and npm
- **Docker**: Use included Dockerfiles for containerized deployment
- **Static Export**: Build frontend as static files for CDN hosting

### Environment Configuration
- **Frontend**: `NEXT_PUBLIC_API_URL` - Your backend API URL
- **Backend**: No environment variables needed (users provide API keys)

For detailed deployment instructions, see `DEPLOYMENT_PROFESSIONAL.md`

## 📋 Features

### ✅ Current Features

- **Single Company Discovery**: Enter company name and optional URL
- **Batch Processing**: Process up to 50 companies at once
- **Real-time Status**: Track job progress with live updates
- **User API Keys**: Secure - users provide their own API keys
- **Export Options**: Results available in JSON format
- **Modern UI**: Clean, responsive interface with Tailwind CSS

### 🚧 Planned Features

- CSV file upload for batch processing
- Export to Excel and CSV formats
- Integration with actual discovery workflow
- Download links for results
- Job history and persistence
- Advanced filtering and search

## 🔑 API Keys Required

Users must provide their own API keys through the frontend:

### OpenAI API Key (Required)
- Get at: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Used for: AI-powered analysis and location extraction

### Google Maps API Key (Optional, Recommended)
- Get at: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Enable: Places API, Geocoding API
- Used for: Location validation and geocoding

### Tavily API Key (Optional)
- Get at: [tavily.com](https://tavily.com)
- Used for: Enhanced web search capabilities

## 📡 API Endpoints

### Health & Info
- `GET /` - API information and health check
- `GET /health` - Simple health check

### Discovery
- `POST /discover/single` - Discover single company locations
- `POST /discover/batch` - Batch process multiple companies

### Jobs
- `GET /jobs/{job_id}/status` - Get job status
- `GET /jobs/{job_id}/results` - Get job results
- `GET /jobs` - List recent jobs
- `DELETE /jobs/{job_id}` - Delete job

## 🔧 Development

### Project Structure

```
My-own-project/
├── api/                    # FastAPI backend
│   ├── main.py            # Main FastAPI application
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Docker configuration
│   └── railway.json      # Railway deployment config
├── frontend/              # Next.js frontend
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # Utilities and API client
│   ├── package.json      # Node.js dependencies
│   ├── Dockerfile         # Docker configuration
│   └── railway.json      # Railway deployment config
└── README.md             # This file
```

### Key Files

- `api/main.py` - FastAPI backend with all endpoints
- `frontend/app/page.tsx` - Main frontend page
- `frontend/components/CompanyForm.tsx` - Company discovery form
- `frontend/lib/api.ts` - API client for backend communication

## 🛡️ Security

- **No server-side API key storage**: Users provide their own keys
- **CORS enabled**: Configured for cross-origin requests
- **Input validation**: All inputs validated on both frontend and backend
- **Error handling**: Comprehensive error handling and user feedback

## 📝 Usage

1. **Open the frontend** in your browser
2. **Enter your API keys** (click "Show API Keys")
3. **Enter company information**:
   - Company name (required)
   - Company website (optional, but recommended)
4. **Click "Start Discovery"**
5. **Monitor progress** in real-time
6. **View results** when complete

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Make sure to comply with API terms of service for all integrated services.

## 🆘 Support

- Check the API documentation at `/docs` endpoint
- Review browser console for frontend errors
- Check backend logs for API issues
- Ensure all API keys are valid and have sufficient credits

---

**Note**: This system is designed for legitimate business research purposes. Always respect robots.txt files and website terms of service when scraping data.
