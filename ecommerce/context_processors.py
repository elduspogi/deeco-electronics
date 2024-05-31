from .cart import UserCart

def cart(request):
    return {'cart': UserCart(request)}