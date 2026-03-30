# orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from .models import Order, OrderItem
from products.models import Product
from cart.views import get_cart
from decimal import Decimal

@login_required
def order_history(request):
    """Display user's order history"""
    orders = request.user.orders.all()
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_history.html', context)

def checkout(request):
    """Checkout process"""
    cart = get_cart(request)
    cart_items = cart.items.all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Lock products to prevent race conditions
                product_ids = [item.product_id for item in cart_items]
                products = Product.objects.select_for_update().filter(id__in=product_ids)
                product_map = {p.id: p for p in products}

                # Verify stock and decrement (reserve)
                for item in cart_items:
                    product = product_map.get(item.product_id)
                    if not product or product.stock_quantity < item.quantity:
                        raise ValueError(f"Not enough stock for {item.product.name}")
                    
                    product.stock_quantity -= item.quantity
                    product.save()

                # Create order
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    order_number=generate_order_number(),
                    shipping_name=request.POST.get('shipping_name'),
                    shipping_email=request.POST.get('shipping_email'),
                    shipping_phone=request.POST.get('shipping_phone'),
                    shipping_address=request.POST.get('shipping_address'),
                    shipping_city=request.POST.get('shipping_city'),
                    shipping_postal_code=request.POST.get('shipping_postal_code'),
                    shipping_country=request.POST.get('shipping_country'),
                    payment_method=request.POST.get('payment_method'),
                    subtotal=cart.total_price,
                    shipping_cost=Decimal('10.00'),  # Fixed shipping cost
                    tax_amount=cart.total_price * Decimal('0.1'),  # 10% tax
                    total_amount=cart.total_price + Decimal('10.00') + (cart.total_price * Decimal('0.1')),
                )
                
                # Create order items
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.get_price,
                    )
                
                # Clear cart
                cart_items.delete()
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('cart:cart_detail')
            
        # Store order_number in session for guest access
        request.session[f'order_{order.order_number}'] = True
        
        messages.success(request, f'Order {order.order_number} placed successfully!')
        return redirect('orders:order_confirmation', order_number=order.order_number)
    
    # Calculate totals
    subtotal = cart.total_price
    shipping = Decimal('10.00')
    tax = subtotal * Decimal('0.1')
    total = subtotal + shipping + tax
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    return render(request, 'orders/checkout.html', context)

def order_detail(request, order_number):
    """Display order details"""
    if request.user.is_authenticated:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    else:
        if not request.session.get(f'order_{order_number}'):
            messages.error(request, "You don't have permission to view this order.")
            return redirect('products:home')
        order = get_object_or_404(Order, order_number=order_number)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/order_detail.html', context)

def order_confirmation(request, order_number):
    """Order confirmation page"""
    if request.user.is_authenticated:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    else:
        if not request.session.get(f'order_{order_number}'):
            messages.error(request, "You don't have permission to view this order.")
            return redirect('products:home')
        order = get_object_or_404(Order, order_number=order_number)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/order_confirmation.html', context)

def generate_order_number():
    """Generate unique order number"""
    return f"ORD-{get_random_string(8).upper()}"