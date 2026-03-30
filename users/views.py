# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django_ratelimit.decorators import ratelimit

class CustomLoginView(auth_views.LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, 'Welcome back!')
        return super().form_valid(form)

    @ratelimit(key='ip', rate='5/m', method='POST', block=True)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class CustomLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)

@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('products:home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('users:login')
    else:
        form = UserCreationForm()

    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    recent_orders = request.user.orders.all()[:5] if hasattr(request.user, 'orders') else []
    wishlist_count = request.user.wishlist.total_items if hasattr(request.user, 'wishlist') else 0

    context = {
        'recent_orders': recent_orders,
        'wishlist_count': wishlist_count,
    }
    return render(request, 'users/profile.html', context)