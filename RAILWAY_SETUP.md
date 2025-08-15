# 🚂 Railway Deployment Setup

## 🎯 **Quick Setup Guide**

### **Step 1: Deploy to Railway**
1. Go to [Railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your MinuteMate repository
4. Railway will automatically build and deploy

### **Step 2: Add Environment Variables**
In Railway dashboard → Variables tab, add:

| Variable Name | Description | Required |
|---------------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key from platform.openai.com | ✅ Yes |
| `SECRET_KEY` | Random secret for sessions | Recommended |

### **Step 3: Add PostgreSQL (Optional)**
1. Click "New Service" → "PostgreSQL"
2. Railway automatically sets `DATABASE_URL`
3. Improves performance over SQLite

### **Step 4: Verify Deployment**
- Check health: `https://your-app.railway.app/api/health`
- Access frontend: `https://your-app.railway.app/frontend/`

## 🔑 **Getting Your OpenAI API Key**

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up and add billing information
3. Navigate to API Keys → Create new secret key
4. Copy the key (starts with `sk-`)
5. Add to Railway environment variables

## 💰 **Cost Estimates**
- **Whisper:** ~$0.006 per minute of audio
- **GPT-4:** ~$0.03 per 1K tokens
- **Typical meeting:** $0.50 - $2.00

## 🛠️ **Troubleshooting**

**Build fails:** Check requirements.txt compatibility
**API key errors:** Verify key is set in Railway variables
**Database issues:** Add PostgreSQL service for better performance

## 📞 **Support**
- Railway docs: [docs.railway.app](https://docs.railway.app)
- OpenAI docs: [platform.openai.com/docs](https://platform.openai.com/docs)
