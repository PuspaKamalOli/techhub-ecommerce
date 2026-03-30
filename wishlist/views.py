# wishlist/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Wishlist, WishlistItem
from products.models import Product

@login_required
def wishlist_detail(request):
    """Display user's wishlist"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = wishlist.items.all()
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist/wishlist_detail.html', context)

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    wishlist_item, created = WishlistItem.objects.get_or_create(
        wishlist=wishlist,
        product=product
    )
    
    if created:
        messages.success(request, f'{product.name} added to your wishlist.')
    else:
        messages.info(request, f'{product.name} is already in your wishlist.')
    
    return redirect('products:product_detail', slug=product.slug)

@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    
    try:
        wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product=product)
        wishlist_item.delete()
        messages.success(request, f'{product.name} removed from your wishlist.')
    except WishlistItem.DoesNotExist:
        messages.error(request, 'Product not found in your wishlist.')
    
    return redirect('wishlist:wishlist_detail')