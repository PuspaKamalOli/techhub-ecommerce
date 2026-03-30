from django.conf import settings

def analytics(request):
    """Add analytics variables to template context"""
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None),
        'FACEBOOK_PIXEL_ID': getattr(settings, 'FACEBOOK_PIXEL_ID', None),
        'TWITTER_PIXEL_ID': getattr(settings, 'TWITTER_PIXEL_ID', None),
    }
