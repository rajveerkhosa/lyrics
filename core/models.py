from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


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
    album = models.CharField(max_length=200, blank=True, null=True)
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


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    favorite_songs = models.ManyToManyField(Song, blank=True, related_name='favorited_by')
    favorite_artists = models.ManyToManyField(Artist, blank=True, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username}'s profile"


class SongComment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} on {self.song.title}"


class ArtistComment(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} on {self.artist.name}"


class SongRating(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('song', 'user')

    def __str__(self) -> str:
        return f"{self.user.username} rated {self.song.title}: {self.rating}/5"


class ArtistRating(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('artist', 'user')

    def __str__(self) -> str:
        return f"{self.user.username} rated {self.artist.name}: {self.rating}/5"


class PageView(models.Model):
    """Track page views for analytics"""
    CONTENT_TYPE_CHOICES = [
        ('song', 'Song'),
        ('artist', 'Artist'),
        ('album', 'Album'),
        ('home', 'Home'),
        ('other', 'Other'),
    ]

    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='other')
    content_id = models.IntegerField(null=True, blank=True)  # ID of the song/artist/etc
    content_title = models.CharField(max_length=500, blank=True)  # Title for display
    url = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['-viewed_at']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self) -> str:
        return f"{self.content_type}: {self.content_title or self.url} at {self.viewed_at}"


class SiteStats(models.Model):
    """Aggregate site statistics updated daily"""
    date = models.DateField(unique=True)
    total_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)  # Based on IP + session
    unique_ips = models.IntegerField(default=0)
    registered_user_views = models.IntegerField(default=0)
    anonymous_views = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Site Statistics'
        verbose_name_plural = 'Site Statistics'

    def __str__(self) -> str:
        return f"Stats for {self.date}: {self.total_views} views, {self.unique_visitors} unique visitors"
