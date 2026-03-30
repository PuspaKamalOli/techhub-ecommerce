# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['get_total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_status', 'total_amount', 'is_active', 'created_at']
    list_filter = ['status', 'payment_status', 'is_active', 'created_at']
    search_fields = ['order_number', 'user__username', 'shipping_email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method', 'is_active')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_email', 'shipping_phone', 'shipping_address', 
                      'shipping_city', 'shipping_postal_code', 'shipping_country')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'total_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'get_total_price']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'product__name']