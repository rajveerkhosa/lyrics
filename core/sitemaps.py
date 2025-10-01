from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Artist, Song, Album


class ArtistSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Artist.objects.all()

    def location(self, obj):
        return reverse("artist_detail", kwargs={"artist": obj.slug})


class AlbumSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Album.objects.select_related("artist").all()

    def location(self, obj):
        return reverse(
            "album_detail",
            kwargs={"artist": obj.artist.slug, "album": obj.slug},
        )


class SongSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Song.objects.filter(is_published=True).select_related("artist")

    def location(self, obj):
        return reverse(
            "song_detail",
            kwargs={"artist": obj.artist.slug, "song": obj.slug},
        )
