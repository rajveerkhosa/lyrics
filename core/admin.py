from django.contrib import admin
from .models import Artist, Song, Line

class LineInline(admin.TabularInline):
    model = Line
    extra = 0

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "year", "is_published")
    list_filter = ("artist", "is_published")
    search_fields = ("title", "artist__name")
    inlines = [LineInline]

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
