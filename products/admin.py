from django.contrib import admin
from .models import Category, Product, ProductImage, ProductReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description', 'created_at', 'is_active']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']

    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discount_price', 'availability', 'featured', 'is_active', 'created_at']
    list_filter = ['category', 'availability', 'featured', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'availability', 'featured', 'is_active']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return self.model.all_objects.select_related('category').prefetch_related('images')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'sku')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'discount_percentage')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'availability')
        }),
        ('Display', {
            'fields': ('featured', 'image', 'is_active')
        }),
        ('Specifications', {
            'fields': ('specifications',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image', 'alt_text', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    ordering = ['product', '-is_primary']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
