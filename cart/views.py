# cart/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from products.models import Product

def get_cart(request):
    """Get or create cart for current user/session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def cart_detail(request):
    """Display cart contents"""
    cart = get_cart(request)
    from django.db.models import prefetch_related_objects
    prefetch_related_objects([cart], 'items__product')
    cart_items = cart.items.all()

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'cart/cart_detail.html', context)

@require_POST
def add_to_cart(request, product_id):
    """Add product to cart — supports AJAX (returns JSON) and standard POST"""
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Check if product is available
    if product.availability != 'in_stock':
        if is_ajax:
            return JsonResponse({'success': False, 'message': f'{product.name} is not available.'})
        messages.error(request, f'{product.name} is not available.')
        return redirect('products:product_detail', slug=product.slug)

    # Check stock
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    msg = ''
    if cart_item.quantity > product.stock_quantity:
        cart_item.quantity = product.stock_quantity
        cart_item.save()
        msg = f'Only {product.stock_quantity} items available for {product.name}.'
    else:
        msg = f'{product.name} added to cart.'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_count': cart.total_items,
        })

    messages.success(request, msg)
    return redirect('cart:cart_detail')

@require_POST
def update_cart(request, item_id):
    """Update cart item quantity"""
    cart = get_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if quantity > 0:
        if quantity <= cart_item.product.stock_quantity:
            cart_item.quantity = quantity
            cart_item.save()
            msg = 'Cart updated successfully.'
        else:
            msg = f'Only {cart_item.product.stock_quantity} items available.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg, 'cart_count': cart.total_items})
    else:
        cart_item.delete()
        msg = 'Item removed from cart.'

    if is_ajax:
        return JsonResponse({'success': True, 'message': msg, 'cart_count': cart.total_items})

    messages.success(request, msg)
    return redirect('cart:cart_detail')

@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart = get_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart.',
            'cart_count': cart.total_items,
        })

    messages.success(request, f'{product_name} removed from cart.')
    return redirect('cart:cart_detail')

def clear_cart(request):
    """Clear all items from cart"""
    cart = get_cart(request)
    cart.items.all().delete()
    messages.success(request, 'Cart cleared successfully.')
    return redirect('cart:cart_detail')