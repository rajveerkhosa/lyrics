# Lyrics Library

A Django web application for displaying Punjabi song lyrics with English translations, romanization, and original text.

## Features

- 🎵 Browse songs by artist, album, or popularity
- 📊 Weekly top charts based on views
- 🌐 Trilingual display: Punjabi, Romanization, and English translation
- 👤 User accounts with favorites and ratings
- 💬 Comments and ratings for songs and artists
- 📈 Analytics dashboard with page view tracking
- 🔍 Search functionality across songs and lyrics
- 📱 Responsive design with Tailwind CSS

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Run Locally

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <your-repo-url>
   cd lyrics
   ```

2. **Start the application**:
   ```bash
   docker-compose up --build
   ```

3. **Access the site**: Open `http://localhost:8000` in your browser

4. **Create an admin user**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access admin panel**: Go to `http://localhost:8000/admin`

### Stop the Application

```bash
docker-compose down
```

## Development Setup (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js 18+ (for Tailwind CSS)

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node dependencies**:
   ```bash
   npm install
   ```

4. **Build Tailwind CSS**:
   ```bash
   npm run tw:build
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

### Development with Live Tailwind Watching

In a separate terminal, run:
```bash
npm run tw:watch
```

This will automatically rebuild CSS when you modify templates.

## Project Structure

```
lyrics/
├── core/                  # Main Django app
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── admin.py          # Admin configuration
│   ├── middleware.py     # Page view tracking
│   └── migrations/       # Database migrations
├── lyricslib/            # Project settings
│   ├── settings.py       # Django settings
│   ├── urls.py           # URL configuration
│   └── wsgi.py          # WSGI configuration
├── templates/            # HTML templates
├── static/               # Static files (CSS, JS)
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
└── requirements.txt     # Python dependencies
```

## Environment Variables

Create a `.env` file (see `.env.example`) with:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=  # Optional: PostgreSQL URL for production
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions for:
- 🐳 Docker deployment (recommended)
- Render
- Railway
- Heroku
- DigitalOcean, AWS, Google Cloud

## Technology Stack

- **Backend**: Django 5.2
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Frontend**: Tailwind CSS
- **Server**: Gunicorn
- **Static Files**: WhiteNoise
- **Containerization**: Docker

## Features in Detail

### Analytics Dashboard
- Track page views for songs, artists, and albums
- Weekly trending charts
- Site-wide statistics

### User Features
- Create account and login
- Favorite songs and artists
- Rate songs and artists (1-5 stars)
- Comment on songs and artists
- View personal profile

### Admin Panel
- Manage artists, albums, and songs
- Bulk import lyrics via CSV
- Create albums dynamically when adding songs
- Filter albums by selected artist
- Analytics dashboard with view counts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to use this project for your own purposes.

## Support

For issues or questions, please open an issue on GitHub.
