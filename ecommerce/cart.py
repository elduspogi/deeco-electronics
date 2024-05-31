from .models import *

class UserCart():
    def __init__(self, request):
        self.session = request.session
        self.request = request

        cart = self.session.get('session_key')

        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}

        self.cart = cart
    
    def db_add(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)

        if product_id in self.cart:
            pass
            # self.cart[product_id]['quantity'] += quantity
        else:
            self.cart[product_id] = int(product_qty)

        self.session.modified = True

        if self.request.user.is_authenticated:
            current_user = User.objects.filter(id=self.request.user.id)
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            current_user.update(old_cart=str(carty))

    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = int(quantity)

        if product_id in self.cart:
            pass
            # self.cart[product_id]['quantity'] += quantity
        else:
            self.cart[product_id] = int(product_qty)

        self.session.modified = True

        if self.request.user.is_authenticated:
            current_user = User.objects.filter(id=self.request.user.id)
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            current_user.update(old_cart=str(carty))

    def __len__(self):
        return len(self.cart)
    
    def get_products(self):
        product_ids = self.cart.keys()

        products = Product.objects.filter(id__in=product_ids)

        return products
    
    def get_guest_products(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            product_id = str(product.id)
            if isinstance(self.cart[product_id], dict):
                product.quantity = self.cart[product_id]['quantity']
            else:
                product.quantity = self.cart[product_id]
        return products
    
    def get_quantities(self):
        quantities = self.cart
        print(quantities)
        return quantities
    
    def update(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)

        user_cart = self.cart

        user_cart[product_id] = product_qty

        self.session.modified = True

        updated_cart = self.cart

        return updated_cart
    
    def delete(self, product):
        product_id = str(product)

        if product_id in self.cart:
            del self.cart[product_id]

        self.session.modified = True

        if self.request.user.is_authenticated:
            current_user = User.objects.filter(id=self.request.user.id)
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            current_user.update(old_cart=str(carty))

    def get(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            pass

    def remove_checked_out_products(self, request, checked_out_product_ids):
        for product_id in checked_out_product_ids:
            if str(product_id) in self.cart:
                del self.cart[str(product_id)]
        # Save changes to the session
        request.session.modified = True

    # def cart_total(self):
    #     # Get product IDS
    #     product_ids = self.cart.keys()
    #     # lookup those keys in our products database model
    #     products = Product.objects.filter(id__in=product_ids)
    #     # Get quantities
    #     quantities = self.cart
    #     # Start counting at 0
    #     total = 0
        
    #     for key, value in quantities.items():
    #         # Convert key string into into so we can do math
    #         key = int(key)
    #         for product in products:
    #             if product.id == key:
    #                 if product.is_sale:
    #                     total = total + (product.sale_price * value)
    #                 else:
    #                     total = total + (product.price * value)
    #     return total