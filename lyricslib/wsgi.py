"""
WSGI config for lyricslib project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / '.env.local'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lyricslib.settings")

application = get_wsgi_application()
