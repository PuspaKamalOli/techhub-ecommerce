from django.contrib import admin

# Register your models here.
# wishlist/admin.py
from django.contrib import admin
from .models import Wishlist, WishlistItem

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'created_at']
    search_fields = ['user__username']
    inlines = [WishlistItemInline]

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['product__name', 'wishlist__user__username']