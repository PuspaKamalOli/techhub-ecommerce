# products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from datetime import timedelta
from .models import Product, Category, ProductReview, ProductImage
from orders.models import Order
from payment_processing.models import Payment

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """Analytics dashboard for e-commerce metrics"""
    
    # Get basic metrics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_sales = Order.objects.filter(status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Get payment metrics
    try:
        from payment_processing.models import Payment
        total_payments = Payment.objects.filter(status='completed').count()
        recent_payments = Payment.objects.select_related('order').order_by('-created_at')[:5]
    except ImportError:
        total_payments = 0
        recent_payments = []
    
    # Get recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Get category statistics with percentage calculation
    category_stats = []
    if total_products > 0:
        categories = Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)
        
        for category in categories:
            percentage = round((category.product_count / total_products) * 100, 1)
            category_stats.append({
                'name': category.name,
                'product_count': category.product_count,
                'percentage': percentage
            })
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'total_payments': total_payments,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'category_stats': category_stats,
    }
    
    return render(request, 'products/analytics_dashboard.html', context)

def home(request):
    """Homepage with featured products and categories (cached 10 min)"""
    cache_key = 'home_featured_products'
    featured_products = cache.get(cache_key)
    if featured_products is None:
        featured_products = list(
            Product.objects.with_bayesian_score().filter(
                featured=True, availability='in_stock'
            ).select_related('category').prefetch_related('images').order_by('-bayesian_score')[:8]
        )
        cache.set(cache_key, featured_products, 600)

    categories = Category.objects.all()[:4]
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'products/home.html', context)

def product_list(request):
    """Display all products with filtering and pagination"""
    products = Product.objects.with_bayesian_score().filter(availability='in_stock').select_related('category').prefetch_related('images')
    categories = Category.objects.all()
    
    # Category filtering
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Price filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', 'highest_rated')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-bayesian_score', '-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'current_sort': sort_by,
    }
    return render(request, 'products/product_list.html', context)

def search_autocomplete(request):
    """Return JSON product suggestions for search autocomplete"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    cache_key = f'autocomplete_{query.lower()[:30]}'
    results = cache.get(cache_key)
    if results is None:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query),
            availability='in_stock'
        ).select_related('category')[:8]
        results = [
            {
                'name': p.name,
                'slug': p.slug,
                'category': p.category.name,
                'price': str(p.get_price),
                'url': p.get_absolute_url(),
            }
            for p in products
        ]
        cache.set(cache_key, results, 300)  # Cache autocomplete 5 min
    return JsonResponse({'results': results})

def product_detail(request, slug):
    """Display individual product details"""
    product = get_object_or_404(Product.objects.select_related('category').prefetch_related('images'), slug=slug)
    related_products = Product.objects.with_bayesian_score().filter(
        category=product.category,
        availability='in_stock'
    ).exclude(id=product.id).select_related('category').prefetch_related('images').order_by('-bayesian_score')[:4]
    
    reviews = product.reviews.select_related('user').all().order_by('-created_at')
    
    # Check if user has this product in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = request.user.wishlist.items.filter(product=product).exists() if hasattr(request.user, 'wishlist') else False
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'products/product_detail.html', context)

def category_detail(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.with_bayesian_score().filter(
        category=category, availability='in_stock'
    ).select_related('category').prefetch_related('images').order_by('-bayesian_score', '-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'products/category_detail.html', context)

def search(request):
    """Search products by name and description"""
    query = request.GET.get('q', '')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.with_bayesian_score().filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            availability='in_stock'
        ).select_related('category').prefetch_related('images').distinct().order_by('-bayesian_score')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'total_results': products.count(),
    }
    return render(request, 'products/search_results.html', context)

@login_required
@ratelimit(key='user', rate='3/h', method='POST', block=True)
def add_review(request, slug):
    """Handle product review submissions (rate-limited: 3/hr per user)"""
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        rating_val = request.POST.get('rating')
        comment = request.POST.get('comment')

        try:
            rating = float(rating_val)
            if rating not in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
                raise ValueError("Invalid rating value")
        except (TypeError, ValueError):
            messages.error(request, "Please provide a valid star rating.")
            return redirect('products:product_detail', slug=slug)

        if comment and comment.strip():
            review, created = ProductReview.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={'rating': rating, 'comment': comment.strip()}
            )
            # Invalidate cached rankings so new review is reflected
            cache.delete('home_featured_products')
            cache.delete_many([
                f'product_list_highest_rated_page1',
                f'category_{product.category.slug}_page1',
            ])
            if created:
                messages.success(request, "Your review has been added!")
            else:
                messages.success(request, "Your review has been updated!")
        else:
            messages.error(request, "Please provide a comment for your review.")

    return redirect('products:product_detail', slug=slug)