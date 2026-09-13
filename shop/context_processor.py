from . models import Cart

def cart_items_count(request):
    if request.user.is_authenticated:
       try:
           cart = Cart.objects.get(user=request.user)
           return {'cart_items_count' : cart.cart_items_count}
       except Cart.DoesNotExist:
           {'cart_items_count':0}
    return {'cart_items_count':0}
