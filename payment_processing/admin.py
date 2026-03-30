from django.contrib import admin
from .models import Payment, PaymentMethod

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'user', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order__order_number', 'user__username', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'user', 'amount', 'currency', 'payment_method', 'status')
        }),
        ('Stripe Information', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id', 'transaction_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'card_brand', 'card_last4', 'card_exp_month', 'card_exp_year', 'is_default', 'created_at']
    list_filter = ['card_brand', 'is_default', 'created_at']
    search_fields = ['user__username', 'stripe_payment_method_id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
