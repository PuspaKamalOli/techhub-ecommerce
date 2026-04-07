# AI/tools.py
"""
Database tools for the chatbot agent.
These tools allow the chatbot to perform CRUD operations on user data.
All operations are scoped to the authenticated user for security.

NOTE: These tools require Django to be initialized.
They are called from chatbot/views.py which runs in a Django context,
so Django will already be set up when these tools are used.
"""
import os
import django

# Setup Django if not already configured
# This is needed when tools are imported outside Django context
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techhub.settings')
    django.setup()

from langchain_core.tools import tool
from django.contrib.auth.models import User
from products.models import Product, Category, ProductReview
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from wishlist.models import Wishlist, WishlistItem
from decimal import Decimal
import json


@tool
def get_user_orders(user_id: int) -> str:
    """
    Get all orders for a specific user.
    Args:
        user_id: The ID of the user whose orders to retrieve
    Returns:
        JSON string containing order information
    """
    try:
        user = User.objects.get(id=user_id)
        orders = Order.objects.filter(user=user).order_by('-created_at')
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'order_number': order.order_number,
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': str(order.total_amount),
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'items_count': order.items.count()
            })
        
        return json.dumps({
            'success': True,
            'orders': orders_data,
            'total_orders': len(orders_data)
        })
    except User.DoesNotExist:
        return json.dumps({'success': False, 'error': 'User not found'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def get_user_cart(user_id: int) -> str:
    """
    Get cart contents for a specific user.
    Args:
        user_id: The ID of the user whose cart to retrieve
    Returns:
        JSON string containing cart information
    """
    try:
        user = User.objects.get(id=user_id)
        cart, created = Cart.objects.get_or_create(user=user)
        
        cart_items = []
        for item in cart.items.all():
            cart_items.append({
                'product_name': item.product.name,
                'product_id': item.product.id,
                'quantity': item.quantity,
                'price': str(item.product.get_price),
                'total': str(item.get_total_price())
            })
        
        return json.dumps({
            'success': True,
            'cart': {
                'total_items': cart.total_items,
                'total_price': str(cart.total_price),
                'items': cart_items
            }
        })
    except User.DoesNotExist:
        return json.dumps({'success': False, 'error': 'User not found'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> str:
    """
    Add a product to user's cart.
    Args:
        user_id: The ID of the user
        product_id: The ID of the product to add
        quantity: Quantity to add (default: 1)
    Returns:
        JSON string indicating success or failure
    """
    try:
        user = User.objects.get(id=user_id)
        product = Product.objects.get(id=product_id)
        
        if product.availability != 'in_stock' or product.stock_quantity < quantity:
            return json.dumps({
                'success': False,
                'error': f'Product {product.name} is not available in the requested quantity'
            })
        
        cart, created = Cart.objects.get_or_create(user=user)
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not item_created:
            # Item already exists, increment quantity
            cart_item.quantity += quantity
            cart_item.save()
        else:
            # New item was created, ensure it's saved
            cart_item.save()
        
        # Refresh both objects from database to get updated totals
        cart.refresh_from_db()
        cart_item.refresh_from_db()
        
        # Verify the item is actually in the cart
        cart_items_count = CartItem.objects.filter(cart=cart, product=product).count()
        if cart_items_count == 0:
            return json.dumps({
                'success': False,
                'error': f'Failed to add {product.name} to cart - item not found after creation'
            })
        
        return json.dumps({
            'success': True,
            'message': f'Added {quantity} x {product.name} to cart',
            'cart_total_items': cart.total_items,
            'product_name': product.name,
            'product_price': str(product.get_price)
        })
    except (User.DoesNotExist, Product.DoesNotExist) as e:
        return json.dumps({'success': False, 'error': f'Not found: {str(e)}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def remove_from_cart(user_id: int, product_id: int) -> str:
    """
    Remove a product from user's cart.
    Args:
        user_id: The ID of the user
        product_id: The ID of the product to remove
    Returns:
        JSON string indicating success or failure
    """
    try:
        user = User.objects.get(id=user_id)
        cart = Cart.objects.get(user=user)
        product = Product.objects.get(id=product_id)
        
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        if cart_item:
            product_name = cart_item.product.name
            cart_item.delete()
            return json.dumps({
                'success': True,
                'message': f'Removed {product_name} from cart'
            })
        else:
            return json.dumps({
                'success': False,
                'error': 'Product not found in cart'
            })
    except (User.DoesNotExist, Cart.DoesNotExist, Product.DoesNotExist) as e:
        return json.dumps({'success': False, 'error': f'Not found: {str(e)}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def update_cart_item_quantity(user_id: int, product_id: int, quantity: int) -> str:
    """
    Update the quantity of a product in user's cart.
    Args:
        user_id: The ID of the user
        product_id: The ID of the product
        quantity: New quantity (must be > 0)
    Returns:
        JSON string indicating success or failure
    """
    try:
        if quantity <= 0:
            return json.dumps({'success': False, 'error': 'Quantity must be greater than 0'})
        
        user = User.objects.get(id=user_id)
        cart = Cart.objects.get(user=user)
        product = Product.objects.get(id=product_id)
        
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        if cart_item:
            if product.stock_quantity < quantity:
                return json.dumps({
                    'success': False,
                    'error': f'Insufficient stock. Available: {product.stock_quantity}'
                })
            cart_item.quantity = quantity
            cart_item.save()
            return json.dumps({
                'success': True,
                'message': f'Updated {product.name} quantity to {quantity}'
            })
        else:
            return json.dumps({
                'success': False,
                'error': 'Product not found in cart'
            })
    except (User.DoesNotExist, Cart.DoesNotExist, Product.DoesNotExist) as e:
        return json.dumps({'success': False, 'error': f'Not found: {str(e)}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def get_user_wishlist(user_id: int) -> str:
    """
    Get wishlist contents for a specific user.
    Args:
        user_id: The ID of the user whose wishlist to retrieve
    Returns:
        JSON string containing wishlist information
    """
    try:
        user = User.objects.get(id=user_id)
        wishlist, created = Wishlist.objects.get_or_create(user=user)
        
        wishlist_items = []
        for item in wishlist.items.all():
            wishlist_items.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'price': str(item.product.get_price),
                'added_at': item.added_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return json.dumps({
            'success': True,
            'wishlist': {
                'total_items': wishlist.total_items,
                'items': wishlist_items
            }
        })
    except User.DoesNotExist:
        return json.dumps({'success': False, 'error': 'User not found'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def add_to_wishlist(user_id: int, product_id: int) -> str:
    """
    Add a product to user's wishlist.
    Args:
        user_id: The ID of the user
        product_id: The ID of the product to add
    Returns:
        JSON string indicating success or failure
    """
    try:
        user = User.objects.get(id=user_id)
        product = Product.objects.get(id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=user)
        
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        if created:
            return json.dumps({
                'success': True,
                'message': f'Added {product.name} to wishlist'
            })
        else:
            return json.dumps({
                'success': False,
                'error': f'{product.name} is already in your wishlist'
            })
    except (User.DoesNotExist, Product.DoesNotExist) as e:
        return json.dumps({'success': False, 'error': f'Not found: {str(e)}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def remove_from_wishlist(user_id: int, product_id: int) -> str:
    """
    Remove a product from user's wishlist.
    Args:
        user_id: The ID of the user
        product_id: The ID of the product to remove
    Returns:
        JSON string indicating success or failure
    """
    try:
        user = User.objects.get(id=user_id)
        wishlist = Wishlist.objects.get(user=user)
        product = Product.objects.get(id=product_id)
        
        wishlist_item = WishlistItem.objects.filter(
            wishlist=wishlist,
            product=product
        ).first()
        
        if wishlist_item:
            product_name = wishlist_item.product.name
            wishlist_item.delete()
            return json.dumps({
                'success': True,
                'message': f'Removed {product_name} from wishlist'
            })
        else:
            return json.dumps({
                'success': False,
                'error': 'Product not found in wishlist'
            })
    except (User.DoesNotExist, Wishlist.DoesNotExist, Product.DoesNotExist) as e:
        return json.dumps({'success': False, 'error': f'Not found: {str(e)}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def search_products(query: str) -> str:
    """
    Search for products by name, description, or category.
    Uses case-insensitive partial matching for better results.
    Args:
        query: Search query string (e.g. "laptops", "samsung phone")
    Returns:
        JSON string containing matching products
    """
    try:
        from django.db.models import Q

        # Split query into words for better matching
        query_words = query.lower().strip().split()
        
        # Build Q objects for each word
        q_objects = Q()
        for word in query_words:
            if len(word) > 2:  # Ignore very short words
                q_objects |= Q(name__icontains=word) | Q(description__icontains=word) | Q(category__name__icontains=word)
        
        # If no words, search the whole query
        if not q_objects:
            q_objects = Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query)
        
        # Filter products
        products = Product.objects.filter(q_objects).distinct()
        
        # Prioritize in-stock products, return up to 10 results
        products = products.order_by('-availability', 'name')[:10]
        
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'price': str(product.get_price),
                'availability': product.availability,
                'category': product.category.name,
                'slug': product.slug
            })
        
        return json.dumps({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def semantic_search_products(query: str) -> str:
    """
    Use this to semantically search for products based on complex or abstract user requests.
    Examples: 'headphones for running in the rain', 'a cheap laptop for coding'.
    This uses AI embeddings to mathematically match the meaning of the query.
    Args:
        query: Search query string describing the desired product concept.
    Returns:
        JSON string containing conceptually matching products.
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from pgvector.django import CosineDistance
        
        # We use a fast, small embedding model designed for sentence similarity
        embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        query_vector = embedder.embed_query(query)
        
        # Perform Cosine Similarity directly in Neon PostgreSQL
        products = Product.objects.filter(
            embedding__isnull=False, 
            is_active=True,
            availability='in_stock'
        ).annotate(
            distance=CosineDistance('embedding', query_vector)
        ).order_by('distance')[:6]
        
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'price': str(product.get_price),
                'availability': product.availability,
                'category': product.category.name,
                'slug': product.slug,
                'match_distance': float(product.distance)
            })
            
        return json.dumps({
            'success': True,
            'products': products_data,
            'count': len(products_data),
            'note': 'These results are semantically matched via AI.'
        })
    except ImportError:
        return json.dumps({'success': False, 'error': 'AI Embeddings or pgvector not properly configured.'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def get_product_details(product_id: int) -> str:
    """
    Get detailed information about a specific product.
    Args:
        product_id: The ID of the product
    Returns:
        JSON string containing product details
    """
    try:
        product = Product.objects.get(id=product_id)
        
        return json.dumps({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': str(product.price),
                'discount_price': str(product.discount_price) if product.discount_price else None,
                'availability': product.availability,
                'stock_quantity': product.stock_quantity,
                'category': product.category.name,
                'sku': product.sku,
                'specifications': product.specifications
            }
        })
    except Product.DoesNotExist:
        return json.dumps({'success': False, 'error': 'Product not found'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def get_user_profile(user_id: int) -> str:
    """
    Get user profile information.
    Args:
        user_id: The ID of the user
    Returns:
        JSON string containing user profile information
    """
    try:
        user = User.objects.get(id=user_id)
        
        return json.dumps({
            'success': True,
            'profile': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'total_orders': user.orders.count()
            }
        })
    except User.DoesNotExist:
        return json.dumps({'success': False, 'error': 'User not found'})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def generate_checkout_link(user_id: int) -> str:
    """
    Generates a secure checkout link for the user's cart.
    Use this INSTEAD of placing an order automatically so the user can securely review and pay.
    Crucial for Human-in-the-Loop financial confirmation.
    Args:
        user_id: The ID of the authenticated user
    Returns:
        JSON string indicating success or failure with the direct checkout URL sequence.
    """
    try:
        user = User.objects.get(id=user_id)
        cart = Cart.objects.filter(user=user).first()
        
        if not cart or cart.items.count() == 0:
            return json.dumps({
                'success': False,
                'error': 'Your cart is empty. Add items before proceeding to checkout.'
            })

        total = sum(item.get_total_price() for item in cart.items.all())

        return json.dumps({
            'success': True,
            'message': f'Your cart has {cart.items.count()} items totaling ${total}. Please click the link to confirm and securely pay.',
            'checkout_url': '/orders/checkout/',
            'action_required': 'Display this URL directly to the user as a clickable markdown button/link.'
        })

    except User.DoesNotExist:
        return json.dumps({'success': False, 'error': 'User not found.'})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return json.dumps({'success': False, 'error': str(e)})
