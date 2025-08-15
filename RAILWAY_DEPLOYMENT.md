# 🚂 MinuteMate Railway Deployment Guide

## Quick Deployment Steps

### 1. **Prepare Your Repository**
```bash
# Make sure all files are committed
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. **Deploy to Railway**

#### Option A: One-Click Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/minutemate)

#### Option B: Manual Setup
1. Go to [Railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your MinuteMate repository
6. Railway will automatically detect it's a Python app

### 3. **Add Environment Variables**
In Railway dashboard, go to your project → Variables tab:

**Required:**
```
OPENAI_API_KEY=your-openai-api-key-here
```

**Optional but Recommended:**
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### 4. **Add Database (Recommended)**
1. In Railway dashboard, click "New Service"
2. Select "PostgreSQL"
3. Railway will automatically set `DATABASE_URL`

### 5. **Add Redis (Optional)**
1. Click "New Service" 
2. Select "Redis"
3. Railway will automatically set `REDIS_URL`

## 🎯 **What Railway Provides Automatically:**

✅ **Automatic Builds** - Detects Python and installs dependencies  
✅ **Environment Variables** - DATABASE_URL, REDIS_URL set automatically  
✅ **HTTPS Domain** - Secure domain provided instantly  
✅ **Auto-scaling** - Handles traffic spikes  
✅ **Persistent Storage** - Database and files survive deployments  
✅ **Monitoring** - Built-in logs and metrics  

## 🔧 **Configuration Details:**

### **Build Process:**
- Railway uses `requirements.txt` to install dependencies
- Runs `gunicorn` for production server
- Serves static files from `/frontend/` directory

### **Database:**
- PostgreSQL database included (recommended)
- Automatic backups and scaling
- Connection string provided as `DATABASE_URL`

### **File Storage:**
- Uploaded files stored in `/tmp/` (ephemeral)
- For persistent files, consider Railway's volume mounts
- Or integrate with cloud storage (AWS S3, etc.)

## 🚀 **Post-Deployment:**

### **1. Test Your Deployment**
- Visit your Railway app URL
- Test file upload functionality
- Check health endpoint: `https://your-app.railway.app/api/health`

### **2. Configure Custom Domain (Optional)**
1. In Railway dashboard → Settings
2. Add your custom domain
3. Update DNS records as instructed

### **3. Monitor Performance**
- Check Railway dashboard for metrics
- Monitor logs for any issues
- Set up alerts for critical errors

## 🛠️ **Troubleshooting:**

### **Common Issues:**

**Build Fails:**
- Check `requirements.txt` for invalid packages
- Ensure Python version compatibility

**Database Connection Error:**
- Verify `DATABASE_URL` is set
- Check if PostgreSQL service is running

**File Upload Issues:**
- Railway has 100MB request limit
- Consider cloud storage for large files

**OpenAI API Errors:**
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits

### **Logs and Debugging:**
```bash
# View logs in Railway dashboard or CLI
railway logs
```

## 💰 **Pricing:**

**Free Tier:**
- $5 credit per month
- Perfect for testing and development

**Pro Plan:**
- $20/month for production apps
- Includes PostgreSQL and Redis
- Custom domains and advanced features

## 🔄 **Updates and Maintenance:**

### **Automatic Deployments:**
- Push to `main` branch triggers deployment
- Railway rebuilds and redeploys automatically

### **Manual Deployment:**
```bash
# Using Railway CLI
railway login
railway link
railway deploy
```

## 📊 **Monitoring:**

### **Health Checks:**
- Railway monitors `/` endpoint
- Automatic restarts on failures
- Built-in uptime monitoring

### **Performance Metrics:**
- CPU and memory usage
- Request response times
- Error rates and logs

## 🎉 **You're Ready!**

Your MinuteMate application should now be running on Railway with:
- ✅ Secure HTTPS domain
- ✅ PostgreSQL database
- ✅ Automatic scaling
- ✅ Professional monitoring
- ✅ Easy updates via Git

Visit your app and start processing meeting recordings! 🎙️📝
