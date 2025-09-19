from django.contrib import admin
from django.urls import path
from django.contrib.sitemaps.views import sitemap

from core.views import home, search, artist_detail, song_detail
from core.sitemaps import ArtistSitemap, SongSitemap

sitemaps = {"artists": ArtistSitemap, "songs": SongSitemap}

urlpatterns = [
    path("", home, name="home"),
    path("search/", search, name="search"),

    # Artist + Song
    path("a/<slug:artist>/", artist_detail, name="artist_detail"),
    path("a/<slug:artist>/<slug:song>/", song_detail, name="song_detail"),

    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("admin/", admin.site.urls),
]
