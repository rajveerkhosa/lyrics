from django.contrib import admin
from django.urls import path
from django.contrib.sitemaps.views import sitemap

from core import views
from core.sitemaps import ArtistSitemap, SongSitemap

sitemaps = {"artists": ArtistSitemap, "songs": SongSitemap}

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),

    # ✅ Artist and Song routes
    path("a/<slug:artist>/", views.artist_detail, name="artist_detail"),
    path("a/<slug:artist>/<slug:song>/", views.song_detail, name="song_detail"),

    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("admin/", admin.site.urls),
]
