from django.db import models
from django.utils.text import slugify


class Artist(models.Model):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    # Optional fields for the artist page
    image_url = models.URLField(blank=True)
    about = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Song(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    year = models.IntegerField(null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    is_published = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.artist.name}-{self.title}")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} — {self.artist.name}"


class Line(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="lines")
    no = models.IntegerField()
    original = models.TextField()
    romanized = models.TextField(blank=True, null=True)
    translation_en = models.TextField()

    class Meta:
        unique_together = ("song", "no")
        ordering = ["no"]

    def __str__(self) -> str:
        return f"{self.song.title} #{self.no}"
