from .models import Order

def restaurant_context(request):
    if request.user.is_authenticated and hasattr(request.user, 'restaurant'):
        restaurant = request.user.restaurant
        pending_count = Order.objects.filter(restaurant=restaurant, status='PENDING').count()
        cashier_pending_count = Order.objects.filter(restaurant=restaurant, status='DELIVERED', is_paid=False).count()
        return {
            'nav_pending_count': pending_count,
            'nav_cashier_count': cashier_pending_count,
        }
    return {}
