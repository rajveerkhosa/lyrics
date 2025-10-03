from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from django import forms
import csv
import io
from .models import (
    Artist, Album, Song, Line, UserProfile,
    SongComment, ArtistComment, SongRating, ArtistRating,
    PageView, SiteStats
)


class LineInline(admin.TabularInline):
    model = Line
    extra = 0


class SongAdminForm(forms.ModelForm):
    csv_lyrics = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 10,
            'cols': 80,
            'placeholder': 'Paste CSV lyrics here (format: original,romanized,translation_en)\nLeave romanized empty if not needed.\nExample:\n가사1,gasaone,Lyrics 1\n가사2,,Lyrics 2'
        }),
        help_text='Paste CSV formatted lyrics. Format: original,romanized,translation_en (one line per row). This will replace all existing lines.',
        label='CSV Lyrics Import'
    )

    new_album_title = forms.CharField(
        required=False,
        max_length=200,
        help_text='Enter a new album name if the album doesn\'t exist yet',
        label='Or create new album'
    )

    class Meta:
        model = Song
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show existing lines as CSV if editing
        if self.instance.pk:
            lines = self.instance.lines.all().order_by('no')
            if lines:
                csv_data = []
                for line in lines:
                    csv_data.append(f'{line.original},{line.romanized or ""},{line.translation_en}')
                self.fields['csv_lyrics'].initial = '\n'.join(csv_data)

            # Filter albums by the selected artist
            if self.instance.artist:
                self.fields['album'].queryset = Album.objects.filter(artist=self.instance.artist)
            else:
                self.fields['album'].queryset = Album.objects.all()
        else:
            # For new songs, show all albums initially (JavaScript will filter)
            self.fields['album'].queryset = Album.objects.all()
            # Make album not required so the field shows even if empty
            self.fields['album'].required = False

        # Add help text for album field
        self.fields['album'].help_text = 'First select an artist above, then choose an album or create a new one below'
        self.fields['album'].widget.attrs['data-depends-on'] = 'artist'

    def clean(self):
        cleaned_data = super().clean()
        artist = cleaned_data.get('artist')
        album = cleaned_data.get('album')
        new_album_title = cleaned_data.get('new_album_title', '').strip()

        # If new album title is provided, create the album
        if new_album_title and artist:
            album, created = Album.objects.get_or_create(
                title=new_album_title,
                artist=artist,
                defaults={'year': cleaned_data.get('year')}
            )
            cleaned_data['album'] = album

        # Auto-fill year from album if not provided
        if album and album.year and not cleaned_data.get('year'):
            cleaned_data['year'] = album.year

        return cleaned_data


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "year", "has_image")
    list_filter = ("artist", "year")
    search_fields = ("title", "artist__name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("additional_artists",)
    fields = ("artist", "additional_artists", "title", "year", "image", "image_url", "slug")

    def has_image(self, obj):
        return bool(obj.image or obj.image_url)
    has_image.boolean = True
    has_image.short_description = "Image"


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    form = SongAdminForm
    list_display = ("title", "artist", "album", "year", "is_published")
    list_filter = ("artist", "album", "is_published", "year")
    search_fields = ("title", "artist__name", "album__title")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("additional_artists", "featured_artists")
    inlines = [LineInline]
    fields = ("artist", "additional_artists", "title", "album", "new_album_title", "year", "featured_artists", "image", "image_url", "slug", "is_published", "csv_lyrics")

    class Media:
        js = ('admin/js/song_admin.js',)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('get-albums/<int:artist_id>/', self.admin_site.admin_view(self.get_albums_for_artist), name='core_song_get_albums'),
        ]
        return custom_urls + urls

    def get_albums_for_artist(self, request, artist_id):
        from django.http import JsonResponse
        albums = Album.objects.filter(artist_id=artist_id).values('id', 'title')
        return JsonResponse(list(albums), safe=False)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Process CSV lyrics if provided
        csv_lyrics = form.cleaned_data.get('csv_lyrics', '').strip()
        if csv_lyrics:
            # Delete existing lines
            obj.lines.all().delete()

            # Parse and create new lines
            csv_reader = csv.reader(io.StringIO(csv_lyrics))
            line_no = 1
            for row in csv_reader:
                if len(row) >= 2:
                    original = row[0].strip()
                    romanized = row[1].strip() if len(row) > 1 and row[1].strip() else None
                    translation_en = row[2].strip() if len(row) > 2 else ''

                    Line.objects.create(
                        song=obj,
                        no=line_no,
                        original=original,
                        romanized=romanized,
                        translation_en=translation_en
                    )
                    line_no += 1


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email")
    filter_horizontal = ("favorite_songs", "favorite_artists")


@admin.register(SongComment)
class SongCommentAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("song__title", "user__username", "text")


@admin.register(ArtistComment)
class ArtistCommentAdmin(admin.ModelAdmin):
    list_display = ("artist", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("artist__name", "user__username", "text")


@admin.register(SongRating)
class SongRatingAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("song__title", "user__username")


@admin.register(ArtistRating)
class ArtistRatingAdmin(admin.ModelAdmin):
    list_display = ("artist", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("artist__name", "user__username")


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("content_type", "content_title", "user_or_anon", "ip_address", "viewed_at")
    list_filter = ("content_type", "viewed_at", "user")
    search_fields = ("content_title", "url", "ip_address", "user__username")
    readonly_fields = ("content_type", "content_id", "content_title", "url", "ip_address",
                       "user", "session_key", "user_agent", "viewed_at")
    date_hierarchy = "viewed_at"

    def user_or_anon(self, obj):
        return obj.user.username if obj.user else "Anonymous"
    user_or_anon.short_description = "User"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SiteStats)
class SiteStatsAdmin(admin.ModelAdmin):
    list_display = ("date", "total_views", "unique_visitors", "unique_ips",
                    "registered_user_views", "anonymous_views")
    list_filter = ("date",)
    date_hierarchy = "date"
    readonly_fields = ("date", "total_views", "unique_visitors", "unique_ips",
                       "registered_user_views", "anonymous_views")

    def has_add_permission(self, request):
        return False


# Custom admin index with analytics
class AnalyticsDashboard(admin.AdminSite):
    site_header = "Lyrics Library Admin"
    site_title = "Lyrics Admin"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Get stats for last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        seven_days_ago = timezone.now() - timedelta(days=7)
        today = timezone.now().date()

        # Total page views
        total_views = PageView.objects.count()
        views_30d = PageView.objects.filter(viewed_at__gte=thirty_days_ago).count()
        views_7d = PageView.objects.filter(viewed_at__gte=seven_days_ago).count()
        views_today = PageView.objects.filter(viewed_at__date=today).count()

        # Unique visitors (by IP)
        unique_ips_30d = PageView.objects.filter(viewed_at__gte=thirty_days_ago).values('ip_address').distinct().count()
        unique_ips_7d = PageView.objects.filter(viewed_at__gte=seven_days_ago).values('ip_address').distinct().count()
        unique_ips_today = PageView.objects.filter(viewed_at__date=today).values('ip_address').distinct().count()

        # User stats
        from django.contrib.auth.models import User
        total_users = User.objects.count()
        active_users_30d = PageView.objects.filter(
            viewed_at__gte=thirty_days_ago,
            user__isnull=False
        ).values('user').distinct().count()

        # Most viewed content
        top_songs = PageView.objects.filter(content_type='song').values('content_title').annotate(
            views=Count('id')
        ).order_by('-views')[:5]

        top_artists = PageView.objects.filter(content_type='artist').values('content_title').annotate(
            views=Count('id')
        ).order_by('-views')[:5]

        extra_context.update({
            'total_views': total_views,
            'views_30d': views_30d,
            'views_7d': views_7d,
            'views_today': views_today,
            'unique_ips_30d': unique_ips_30d,
            'unique_ips_7d': unique_ips_7d,
            'unique_ips_today': unique_ips_today,
            'total_users': total_users,
            'active_users_30d': active_users_30d,
            'top_songs': top_songs,
            'top_artists': top_artists,
        })

        return super().index(request, extra_context)
