# Deployment Guide

This guide will help you deploy your Lyrics Library Django application to various hosting platforms.

## Prerequisites

1. Your code is in a Git repository
2. You have all the necessary files:
   - `requirements.txt` ✅
   - `Procfile` ✅
   - `runtime.txt` ✅
   - `.env.example` ✅

## Deployment Platforms

### Option 1: Render (Recommended - Free Tier Available)

1. **Create a Render Account**: Go to https://render.com and sign up

2. **Create a Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub/GitLab repository
   - Choose the repository containing your Django app

3. **Configure the Service**:
   - **Name**: `lyrics-library` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave blank
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn lyricslib.wsgi`

4. **Environment Variables** (Add these in Render dashboard):
   ```
   SECRET_KEY=generate-a-new-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.onrender.com
   DATABASE_URL=(Render will provide this automatically if you add PostgreSQL)
   ```

5. **Add PostgreSQL Database** (optional but recommended):
   - In your Render dashboard, create a new PostgreSQL database
   - Copy the "Internal Database URL"
   - Add it as `DATABASE_URL` environment variable

6. **Deploy**: Click "Create Web Service" and wait for deployment!

### Option 2: Railway

1. **Create Railway Account**: Go to https://railway.app and sign up

2. **New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add PostgreSQL**:
   - Click "+ New" → "Database" → "PostgreSQL"
   - Railway will automatically provide DATABASE_URL

4. **Configure Django Service**:
   - Click on your Django service
   - Go to "Variables" tab and add:
     ```
     SECRET_KEY=generate-a-new-secret-key-here
     DEBUG=False
     ALLOWED_HOSTS=your-app.up.railway.app
     ```

5. **Settings**:
   - Go to "Settings" tab
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn lyricslib.wsgi`

6. **Deploy**: Railway will automatically deploy!

### Option 3: Heroku

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

2. **Login and Create App**:
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Add PostgreSQL**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set Environment Variables**:
   ```bash
   heroku config:set SECRET_KEY="generate-a-new-secret-key"
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   ```

## Generate Secret Key

To generate a new SECRET_KEY, run this in Python:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use this command:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Post-Deployment Steps

1. **Create Superuser** (for admin access):
   - Render: Use the "Shell" tab in your service
   - Railway: Use the terminal in your service
   - Heroku: `heroku run python manage.py createsuperuser`

   Then run:
   ```bash
   python manage.py createsuperuser
   ```

2. **Verify Admin Access**:
   - Visit: `https://your-domain.com/admin/`
   - Login with your superuser credentials

3. **Import Your Data**:
   - Use the Django admin to add Artists, Songs, and Lyrics
   - Or import via management commands if you have CSV files

## Troubleshooting

### Static Files Not Loading
- Make sure `python manage.py collectstatic` runs in build command
- Check that WhiteNoise is in MIDDLEWARE (it is!)

### Database Connection Issues
- Verify DATABASE_URL is set correctly
- Check that psycopg2-binary is in requirements.txt (it is!)

### 500 Errors
- Set `DEBUG=True` temporarily to see error details
- Check application logs in your hosting platform
- Verify all environment variables are set

### "DisallowedHost" Error
- Add your domain to ALLOWED_HOSTS environment variable
- Format: `your-domain.com,www.your-domain.com` (comma-separated)

## Custom Domain

After deployment, you can add a custom domain:
- **Render**: Settings → Custom Domain
- **Railway**: Settings → Domains
- **Heroku**: Settings → Domains

## Need Help?

Check your platform's documentation:
- Render: https://render.com/docs/deploy-django
- Railway: https://docs.railway.app/guides/django
- Heroku: https://devcenter.heroku.com/articles/django-app-configuration