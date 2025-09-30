from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import (
    Artist, Song, Line, UserProfile,
    SongComment, ArtistComment, SongRating, ArtistRating,
    PageView, SiteStats
)


class LineInline(admin.TabularInline):
    model = Line
    extra = 0


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "year", "is_published")
    list_filter = ("artist", "is_published", "year")
    search_fields = ("title", "artist__name")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LineInline]


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
