from django.utils.deprecation import MiddlewareMixin
from .models import PageView


class PageViewMiddleware(MiddlewareMixin):
    """Middleware to track page views for analytics"""

    def process_response(self, request, response):
        # Only track successful GET requests (not POST, redirects, errors, etc.)
        if request.method == 'GET' and response.status_code == 200:
            # Skip admin and static file requests
            if not request.path.startswith('/admin/') and not request.path.startswith('/static/'):
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')

                # Determine content type and details
                content_type = 'other'
                content_id = None
                content_title = ''

                path = request.path
                if path == '/' or path.startswith('/charts'):
                    content_type = 'home'
                    content_title = 'Home / Charts'
                elif path.startswith('/a/'):
                    # Could be artist or song
                    parts = path.strip('/').split('/')
                    if len(parts) == 2:  # /a/artist-slug/
                        content_type = 'artist'
                        # Try to get artist from request (if available)
                    elif len(parts) == 3:  # /a/artist-slug/song-slug/
                        content_type = 'song'
                elif path.startswith('/artists'):
                    content_type = 'other'
                    content_title = 'Artists Index'
                elif path.startswith('/albums'):
                    content_type = 'album'
                    content_title = 'Albums Index'
                elif path.startswith('/songs'):
                    content_type = 'other'
                    content_title = 'Songs Index'

                # Create page view record
                try:
                    PageView.objects.create(
                        content_type=content_type,
                        content_id=content_id,
                        content_title=content_title,
                        url=request.path,
                        ip_address=ip_address,
                        user=request.user if request.user.is_authenticated else None,
                        session_key=request.session.session_key or '',
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    )
                except Exception:
                    # Silently fail if tracking fails (don't break the site)
                    pass

        return response