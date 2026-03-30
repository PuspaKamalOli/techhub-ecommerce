from django import template
from django.template.defaultfilters import floatformat
from django.conf import settings

register = template.Library()

@register.filter
def times(value):
    """Returns a range from 1 to value"""
    return range(1, int(value) + 1)

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def discount_percentage(price, discount_price):
    """Calculate discount percentage"""
    if not discount_price or not price:
        return 0
    try:
        percentage = ((float(price) - float(discount_price)) / float(price)) * 100
        return round(percentage, 0)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_primary_image(product):
    """Get the primary image for a product from ProductImage model"""
    if hasattr(product, 'images'):
        primary_image = product.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
    return None
