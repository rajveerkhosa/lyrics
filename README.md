# Punjabi Lyrics Library

A Django web application for browsing Punjabi song lyrics with English translations and romanization. Features comprehensive artist, album, and song management with user engagement tools.

## Features

### Content Management
- **Songs** - Punjabi lyrics with romanization and English translations
- **Artists** - Artist profiles with biographical information
- **Albums** - Album collections with artwork
- **Multiple Artists Support** - Collaborations, additional artists, and featured artists

### User Features
- **User Authentication** - Sign up, login, and profile management
- **Search** - Search songs, artists, albums, and lyric lines
- **Favorites** - Save favorite songs and artists
- **Ratings** - Rate songs and artists (1-5 stars)
- **Comments** - Comment on songs and artists
- **View Tracking** - Track page views and popular content

### Admin Features
- **Private Stats Dashboard** - Comprehensive analytics at `/stats/`
  - User statistics (total, active, new users)
  - Content statistics (songs, albums, artists, ratings, comments)
  - Traffic analytics (page views, unique IPs)
  - Top content (most viewed songs, artists, albums)
- **Django Admin Panel** - Full content management
- **CSV Import** - Bulk import songs from CSV files

## Tech Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite (local) / PostgreSQL (production)
- **Frontend**: Tailwind CSS 3.4
- **Deployment**: Render (with WhiteNoise for static files)
- **Image Processing**: Pillow

## Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+ (for Tailwind CSS)
- pip and npm

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lyrics
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node dependencies**
   ```bash
   npm install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Build Tailwind CSS**
   ```bash
   npm run tw:build
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

10. **Watch Tailwind CSS (optional, in separate terminal)**
    ```bash
    npm run tw:watch
    ```

Visit `http://127.0.0.1:8000` to view the site.

## Environment Variables

### Required
- `SECRET_KEY` - Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)

### Optional
- `DEBUG` - Set to `False` in production (default: `True`)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts (default: `127.0.0.1,localhost`)
- `DATABASE_URL` - PostgreSQL connection string (auto-set by Render)

## Project Structure

```
lyrics/
├── core/                    # Main Django app
│   ├── migrations/         # Database migrations
│   ├── management/         # Custom management commands
│   ├── admin.py           # Admin panel configuration
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py            # URL routing
│   ├── forms.py           # Forms
│   ├── middleware.py      # Custom middleware
│   └── sitemaps.py        # Sitemap configuration
├── lyricslib/             # Project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS)
├── media/                # User uploads (images)
├── .env.example          # Environment variables template
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── package.json          # Node dependencies
```

## Deployment (Render)

The application is configured for deployment on Render.

### Deploy Branch
- Production deploys from `deploy/render` branch
- Render auto-deploys when this branch is updated

### Post-Deployment Steps

1. **Add SECRET_KEY in Render Dashboard**
   - Go to Environment settings
   - Add `SECRET_KEY` with a random 50-character string

2. **Run migrations in Render shell**
   ```bash
   python manage.py migrate
   ```

3. **Create superuser in Render shell**
   ```bash
   python manage.py createsuperuser
   ```

### Files Required for Render
- `requirements.txt` - Python dependencies
- `Procfile` - Web server command: `gunicorn lyricslib.wsgi:application`
- `runtime.txt` - Python version
- Environment variables set in Render dashboard

## Key URLs

- `/` - Home page
- `/songs/` - Browse all songs
- `/artists/` - Browse all artists
- `/albums/` - Browse all albums
- `/charts/` - Top charts (most viewed)
- `/search/` - Search functionality
- `/stats/` - Private analytics dashboard
- `/admin/` - Django admin panel
- `/accounts/login/` - User login
- `/accounts/signup/` - User registration
- `/profile/` - User profile

## Admin Panel Features

Access at `/admin/` with superuser credentials:

- Manage songs, artists, and albums
- Multiple artists support with filter_horizontal
- CSV import for bulk song creation
- Image uploads for artists, albums, and songs
- User and permission management
- View all ratings, comments, and favorites

## Contributing

1. Create feature branch from `main`
2. Make changes and test locally
3. Commit with descriptive messages
4. Push to feature branch
5. Merge to `main` when ready
6. Merge `main` to `deploy/render` for production deployment

## License

All rights reserved.
