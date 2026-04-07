# techhub/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('accounts/', include('users.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('payments/', include('payment_processing.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

from techhub import views

# Serve media files from the PostgreSQL database
urlpatterns += [
    path('db-media/<path:path>', views.serve_neon_db_media, name='neon-db-media')
]