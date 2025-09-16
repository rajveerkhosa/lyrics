from django.db import models
from django.utils.text import slugify

class Artist(models.Model):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *a, **k):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*a, **k)

    def __str__(self):
        return self.name

class Song(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='songs')
    title = models.CharField(max_length=200)
    year = models.IntegerField(null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['artist', 'title'], name='unique_song_per_artist'),
        ]
        ordering = ['title']

    def save(self, *a, **k):
        if not self.slug:
            self.slug = slugify(f"{self.artist.name}-{self.title}")
        super().save(*a, **k)

    def __str__(self):
        return f"{self.title} — {self.artist.name}"

class Line(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='lines')
    no = models.IntegerField()
    original = models.TextField()
    romanized = models.TextField(blank=True, null=True)
    translation_en = models.TextField()

    class Meta:
        unique_together = ("song", "no")
        ordering = ["no"]

    def __str__(self):
        return f"L{self.no}: {self.original[:40]}..."
