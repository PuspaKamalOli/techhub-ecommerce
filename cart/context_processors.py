# cart/context_processors.py
from .models import Cart

def cart(request):
    """Make cart available in all templates"""
    cart_obj = None
    
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        
        cart_obj, created = Cart.objects.get_or_create(session_key=session_key)
    
    from django.db.models import prefetch_related_objects
    prefetch_related_objects([cart_obj], 'items__product')
    return {'cart': cart_obj}