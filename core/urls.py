# core/urls.py
from django.urls import path
from django.contrib.sitemaps.views import sitemap

from . import views
from .sitemaps import ArtistSitemap, SongSitemap

sitemaps = {"artists": ArtistSitemap, "songs": SongSitemap}

urlpatterns = [
    # Home / Top Charts
    path("", views.charts, name="home"),          # base URL = charts
    path("charts/", views.charts, name="charts"),

    # Search
    path("search/", views.search, name="search"),

    # Header links (index pages)
    path("artists/", views.artists_index, name="artists_index"),
    path("albums/", views.albums_index, name="albums_index"),
    path("songs/", views.songs_index, name="songs_index"),

    # Detail pages
    path("a/<slug:artist>/", views.artist_detail, name="artist_detail"),
    path("a/<slug:artist>/<slug:song>/", views.song_detail, name="song_detail"),

    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]
