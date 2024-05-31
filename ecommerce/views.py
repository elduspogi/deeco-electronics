from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.template.loader import render_to_string
from django.db.models import Q, F ,Count
from .cart import UserCart
from .models import User
from .forms import *
import json
from django.utils import timezone
from .decorators import *
from django.core.mail import send_mail
from django.conf import settings
import pytz
from datetime import timedelta
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

current_month = timezone.now().month
current_year = timezone.now().year
current_day = timezone.now().day

# STATUS CHOICES
choices = ['Pending', 'To Pack', 'Ready For Pick Up', 'Picked Up', 'Cancelled']

from_email = settings.DEFAULT_FROM_EMAIL
from_name = settings.MAIL_FROM_NAME

# Create your views here.
@anti_admin
def index(request):
    current_day = timezone.now()

    products = Product.objects.filter(type='Product').exclude(Q(stock=0) | Q(is_deleted=True))
    latest_products = products.order_by('-created_at')[:3]

    bundles = Product.objects.filter(type='Bundle').exclude(Q(stock=0) | Q(is_deleted=True))
    latest_bundles = bundles.order_by('-created_at')[:3]

    reviews = Review.objects.filter(Q(rating='4') | Q(rating='5'))

    return render(request, 'ecommerce/index.html', {'latest_products': latest_products, 'latest_bundles': latest_bundles, 'reviews': reviews})

# Miscellaneous
@anti_admin
def terms_of_service(request):
    return render(request, 'ecommerce/misc/terms-of-service.html')

@anti_admin
def privacy_policy(request):
    return render(request, 'ecommerce/misc/privacy-policy.html')

@anti_admin
def contact(request):
    return render(request, 'ecommerce/user/contact.html')

def login_view(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    if request.user.is_authenticated:
        update_session_auth_hash(request, request.user)
        return redirect('index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)

                current_user = User.objects.get(id=request.user.id)

                if current_user.is_banned:
                    logout(request)
                    messages.error(request, f"Sorry {current_user.name}! You're account has been banned.")
                    return redirect('login')
                
                saved_cart = current_user.old_cart
                if saved_cart:
                    converted_cart = json.loads(saved_cart)
                    cart = UserCart(request)

                    for key,value in converted_cart.items():
                        cart.db_add(product=key, quantity=value)
                        
                if 'next' in request.POST:
                    return redirect(request.POST.get('next'))
                
                if request.user.user_type == 'User':
                    return redirect('shop')
                elif request.user.user_type == 'Admin' or request.user.user_type == 'Superadmin':
                    ActivityLog.objects.create(user=current_user, activity='Logged In', timestamp=manila_time)
                    return redirect('dashboard')
            # else:
            #     messages.error(request, 'Invalid Email and/or Password')
            else:
                form.add_error(None, '')
    else:
        form = LoginForm()

    return render(request, 'ecommerce/auth/login.html', {'form': form})

def logout_view(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    if not request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        current_user = User.objects.get(id=request.user.id)
        if request.user.user_type == 'Admin':
            ActivityLog.objects.create(user=current_user, activity='Logged Out', timestamp=manila_time)

        logout(request)

        messages.success(request, 'You have been logged out. Thanks for stopping by!')
        return redirect('login')
    else:
        return redirect('index')

@anti_admin
def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            name = form.cleaned_data.get('name')
            contact_no = form.cleaned_data.get('contact_no')
            address = form.cleaned_data.get('address')
            password = form.cleaned_data.get('password')
            user_type = 'User'
            
            user = User.objects.create_user(email=email, name=name, contact_no=contact_no, address=address, password=password, user_type=user_type)
            user.email = email
            user.name = name
            user.contact_no = contact_no
            user.address = address
            user.password = password
            user.user_type = user_type
            user.save()

            messages.success(request, 'Registration successful! You can now login. Happy Shopping!')
            return redirect('login')
        else:
            print(form.errors)
            # messages.error(request, form.errors)
    else:
        form = RegisterForm()

    return render(request, 'ecommerce/auth/register.html', {'form': form})
    

# Admin
@login_required
@for_superadmin
def activity_logs(request):
    logs = ActivityLog.objects.all()

    return render(request, 'ecommerce/admin/activity-logs.html', {'logs': logs})

@login_required
@anti_user
def dashboard(request):
    users = User.objects.filter(user_type='User').count()
    total_products = Product.objects.filter(type='Product').count()
    total_bundles = Product.objects.filter(type='Bundle').count()

    pending_orders = Order.objects.filter(status__iexact='Pending').count()
    to_pack_orders = Order.objects.filter(status__iexact='To Pack').count()
    ready_for_pickup_orders = Order.objects.filter(status__iexact='Ready For Pick Up').count()
    picked_up_orders = Order.objects.filter(status__iexact='Picked Up').count()
    cancelled_orders = Order.objects.filter(status__iexact='Cancelled').count()
    
    # Pie Chart Most Product Type Sold
    product_sold_count = OrderItem.objects.filter(product__type='Product').count()
    bundle_sold_count = OrderItem.objects.filter(product__type='Bundle').count()
    pie_chart_data = [product_sold_count, bundle_sold_count]

    # Newly registered Users
    newly_registered_users = User.objects.filter(
        user_type='User',
        date_joined__month=current_month,
        date_joined__year=current_year
    )
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    products_sold = OrderItem.objects.filter(order__order_date__gte=current_month_start).values('product__category').annotate(total_sold=Count('id'))

    category_labels = []
    products_sold_data = []
    for product in products_sold:
        category = Category.objects.get(pk=product['product__category'])
        category_labels.append(category.name)
        products_sold_data.append(product['total_sold'])

    context = {
        'users': users,
        'total_products': total_products,
        'total_bundles': total_bundles,

        'pending_orders': pending_orders,
        'ready_for_pickup_orders': ready_for_pickup_orders,
        'cancelled_orders': cancelled_orders,
        'to_pack_orders': to_pack_orders,
        'picked_up_orders': picked_up_orders,
        
        'pie_chart_data': pie_chart_data,
        'newly_registered_users': newly_registered_users,

        'category_labels': category_labels,
        'products_sold_data': products_sold_data,
    }
    return render(request, 'ecommerce/admin/dashboard.html', context)

@login_required
@anti_user
def add_product(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    categories = Category.objects.all()
    category_count = categories.count()

    if category_count == 0:
        messages.error(request, 'Sorry! Create a category first.')
        return redirect('add_category')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            price = form.cleaned_data['price']
            stock = form.cleaned_data['stock']
            category = form.cleaned_data['category']
            image1 = form.cleaned_data['image1']
            image2 = form.cleaned_data['image2']
            image3 = form.cleaned_data['image3']
            image4 = form.cleaned_data['image4']
            image5 = form.cleaned_data['image5']
            image6 = form.cleaned_data['image6']
            
            product = Product.objects.create(
                name=name, description=description, price=price, 
                stock=stock, category=category, image1=image1, 
                image2=image2, image3=image3, image4=image4, 
                image5=image5, image6=image6)
            
            ActivityLog.objects.create(user=request.user, activity=f'Added Product {product.id}', timestamp=manila_time)

            messages.success(request, 'Product has been added.')
        else:
            print(form.errors)
    else:
        form = ProductForm()

    return render(request, 'ecommerce/admin/add-product.html', {'form': form, 'categories': categories})

@login_required
@anti_user
def edit_product(request, product_id):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    categories = Category.objects.all()
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()

            ActivityLog.objects.create(user=request.user, activity=f'Edited Product {product.id}', timestamp=manila_time)

            messages.success(request, f'Product {product.id} has been updated.')
            return redirect('edit_product', product_id=product.id)
        else:
            messages.error(request, f'Edit of product {product.id} is unsuccessful. Please try again.')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'ecommerce/admin/edit-product.html', {'product': product, 'categories': categories})

@login_required
@anti_user
def edit_category(request, category_id):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    category = Category.objects.get(id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        category.name = name
        category.save()

        ActivityLog.objects.create(user=request.user, activity=f'Edited Category {category.id}', timestamp=manila_time)

        messages.success(request, f'Category {category.id} has been updated.')
        return redirect('edit_category', category_id=category.id)
    
    return render(request, 'ecommerce/admin/edit-category.html', {'category': category})

@login_required
@anti_user
def edit_bundle(request, bundle_id):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    categories = Category.objects.all()
    bundle = get_object_or_404(Product, id=bundle_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=bundle)
        if form.is_valid():
            form.save() 

            ActivityLog.objects.create(user=request.user, activity=f'Edited Bundle {bundle.id}', timestamp=manila_time)

            messages.success(request, f'Product {bundle.id} has been updated.')
            return redirect('edit_bundle', bundle_id=bundle.id)
        else:
            messages.error(request, f'Edit of bundle {bundle.id} is unsuccessful. Please try again.')
    else:
        form = ProductForm(instance=bundle)
    
    return render(request, 'ecommerce/admin/edit-bundle.html', {'bundle': bundle, 'categories': categories})

@login_required
@anti_user
def add_bundle(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    categories = Category.objects.all()
    products = Product.objects.all()

    category_count = categories.count()
    if category_count == 0:
        messages.error(request, 'Sorry! create a category first.')
        return redirect('add_category')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            price = form.cleaned_data['price']
            stock = form.cleaned_data['stock']
            category = form.cleaned_data['category']
            image1 = form.cleaned_data['image1']
            image2 = form.cleaned_data['image2']
            image3 = form.cleaned_data['image3']
            image4 = form.cleaned_data['image4']
            image5 = form.cleaned_data['image5']
            image6 = form.cleaned_data['image6']
            type = 'Bundle'

            product = Product.objects.create(
                name=name, description=description, price=price, 
                stock=stock, category=category, image1=image1, 
                image2=image2, image3=image3, image4=image4, 
                image5=image5, image6=image6, type=type)


            ActivityLog.objects.create(user=request.user, activity=f'Added Bundle {product.id}', timestamp=manila_time)
            messages.success(request, 'Bundle has been added.')
            return redirect('add_bundle')
        else:
            print(form.errors)
    else:
        form = ProductForm()

    context = {
        'form': form, 
        'categories': categories,
        'products': products
    }

    return render(request, 'ecommerce/admin/add-bundle.html', context)

# Add Category
@login_required
@anti_user
def add_category(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    if request.method == 'POST':
        name = request.POST.get('name')

        category = Category.objects.create(name=name)

        ActivityLog.objects.create(user=request.user, activity=f'Added Category {category.name}', timestamp=manila_time)

        messages.success(request, 'Category successfully added.')
        return redirect('add_category')
    
    return render(request, 'ecommerce/admin/add-category.html')

# Product and Bundle List
@login_required
@anti_user
def product_list(request):
    products = Product.objects.filter(Q(type='Product') & Q(is_deleted=False))

    return render(request, 'ecommerce/admin/product-list.html', {'products': products})

@login_required
@anti_user
def bundle_list(request):
    bundles = Product.objects.filter(Q(type='Bundle') & Q(is_deleted=False))

    return render(request, 'ecommerce/admin/bundle-list.html', {'bundles': bundles})

# User and Admin List
@login_required
@anti_user
def user_list(request):
    users = User.objects.filter(Q(user_type='User') & Q(is_banned=False))

    return render(request, 'ecommerce/admin/user-list.html', {'users': users})

@login_required
@anti_user
def category_list(request):
    categories = Category.objects.all()

    return render(request, 'ecommerce/admin/category-list.html', {'categories': categories})

@login_required
@anti_user
def ban_user(request, user_id):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    user = get_object_or_404(User, id=user_id)

    user.is_banned = True
    user.save()

    ActivityLog.objects.create(user=request.user, activity=f'Banned User {user.id}', timestamp=manila_time)

    messages.success(request, f"User {user.name} has been banned.")
    return redirect('user_list')

@login_required
@anti_user
def unban_user(request, user_id):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    user = get_object_or_404(User, id=user_id)

    user.is_banned = False
    user.save()
    
    ActivityLog.objects.create(user=request.user, activity=f'Unbanned User {user.id}', timestamp=manila_time)

    messages.success(request, f"User {user.name} has been unbanned.")
    return redirect('banned_user_list')

@login_required
@anti_user
def banned_user_list(request):
    users = User.objects.filter(Q(user_type='User') & Q(is_banned=True))
    
    return render(request, 'ecommerce/admin/banned-user-list.html', {'users': users})

@login_required
@for_superadmin
def admin_list(request):
    admins = User.objects.filter(user_type='Admin')
    print(admins)
    return render(request, 'ecommerce/admin/admin-list.html', {'admins':admins})

# Admin Registration
@login_required
@for_superadmin
def register_admin(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user_type = 'Admin'

            User.objects.create_user(name=name, email=email, password=password, user_type=user_type)
            messages.success(request, 'Admin created successfully.')
            return redirect('register_admin')
        else:
            messages.error(request, 'There was an error creating an Admin, please try again.')
    else:
        form = AdminRegisterForm()

    return render(request, 'ecommerce/admin/register-admin.html', {'form': form})

# Orders
@login_required
@anti_user
def completed_orders(request):
    completed_orders = Order.objects.filter(status='Picked Up')

    return render(request, 'ecommerce/admin/completed-orders.html', {'completed_orders': completed_orders})

@login_required
@anti_user
def cancelled_orders(request):
    cancelled_orders = Order.objects.filter(status='Cancelled')

    return render(request, 'ecommerce/admin/cancelled-orders.html', {'cancelled_orders': cancelled_orders})

@login_required
@anti_user
def to_pack_orders(request):
    to_pack_orders = Order.objects.filter(Q(status='To Pack') & Q(is_deleted=False))

    return render(request, 'ecommerce/admin/to-pack-orders.html', {'to_pack_orders': to_pack_orders})

@login_required
@anti_user
def ready_for_pickup_orders(request):
    ready_for_pickup_orders = Order.objects.filter(Q(status__iexact='Ready For Pick Up') & Q(is_deleted=False))

    return render(request, 'ecommerce/admin/ready-for-pickup-orders.html', {'ready_for_pickup_orders': ready_for_pickup_orders})

@login_required
@anti_user
def pending_orders(request):
    pending_orders = Order.objects.filter(Q(status='Pending') & Q(is_deleted=False))
    
    return render(request, 'ecommerce/admin/pending-orders.html', {'pending_orders': pending_orders})

@login_required
@anti_user
def edit_order(request, order_id):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    order = get_object_or_404(Order, id=order_id)

    current_user = User.objects.get(id=request.user.id)

    if request.method == 'POST':
        status = request.POST.get('status')

        ActivityLog.objects.create(user=current_user, activity=f'Changed Order Status of Order {order.id} To "{status}"', timestamp=manila_time)

        order.status = status
        order.save()

        if order.status == 'Pending':
            message7 = 'Order status reverted to Pending'
        elif order.status == 'To Pack':
            message7 = 'Your order now is to be packed by us.'
        elif order.status == 'Ready For Pick Up':
            message7 = 'Your order is now ready for pick-up. Please visit our store at the Pickup Date you set.'
        elif order.status == 'Picked Up':
            message7 = 'You picked up your order. Thank you! Shop with us again.'
        elif order.status == 'Cancelled':
            message7 = 'You have cancelled your order.'

        # Format Date
        order_date_formatted = order.order_date.date()
        time_formatted = order.order_date.time()

        subject = 'Order placed at Deeco Electronics.'

        message1 = f'Hi, {order.name}.'
        message2 = 'Your order status has been changed.'
        message3 = f'Order ID: {order.id}'
        message4 = f'Placed At: {order_date_formatted} {time_formatted}'
        message5 = f'Pickup Date: {order.pickup_date}'
        message6 = f'Amount To Pay: ₱ {order.amount}'
        order_status = f'Status: {order.status}'
        message7 = message7
        app_url = settings.APP_URL
        print(order)
        receiver = [order.email]
        # Send Email
        template = 'email.html'
        context = {
            'message1': message1,
            'message2': message2,
            'message3': message3,
            'message4': message4,
            'message5': message5,
            'message6': message6,
            'message7': message7,
            'order_status': order_status,
            'app_url': app_url
        }
        html_message = render_to_string(template, context)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = receiver
        send_mail(subject, '', from_email, to_email, html_message=html_message)

        messages.success(request, f'Order {order.id} status has been changed successfully.')
        return redirect('edit_order', order_id=order.id)
    
    return render(request, 'ecommerce/admin/edit-order.html', {'order': order, 'choices': choices})

# Admin Profile
@login_required
@anti_user
def admin_edit_profile(request):
    user = request.user
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')

        user.name = name
        user.email = email
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('admin_edit_profile')
    
    return render(request, 'ecommerce/admin/edit-profile.html')

@login_required
@anti_user
def admin_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('admin_change_password')
        else:
            messages.error(request, 'There was an error changing the password. Please try again.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'ecommerce/admin/change-password.html', {'form': form})

# User
@login_required
@anti_admin
def profile(request):
    orders = Order.objects.filter(user=request.user)
    order_data = []
    for order in orders:
        order_items = OrderItem.objects.filter(order=order)
        order_data.append({'order': order, 'order_items': order_items})

    if request.method == 'POST':
        user = request.user
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        user.contact_no = request.POST.get('contact_no')
        user.address = request.POST.get('address')
        user.save()

        messages.success(request, 'Profile has been updated.')
        return redirect('profile')

    return render(request, 'ecommerce/user/profile.html', {'orders': orders, 'order_data': order_data})

@login_required
@anti_admin
def user_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated.')
            return redirect('user_change_password')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'ecommerce/user/change-password.html', {'form': form})

@anti_admin
def shop(request):
    products = Product.objects.filter(type='Product').exclude(Q(stock=0) | Q(is_deleted=True))

    bundles = Product.objects.filter(type='Bundle').exclude(Q(stock=0) | Q(is_deleted=True))
    categories = Category.objects.all()

    return render(request, 'ecommerce/user/shop.html', {'products': products, 'bundles': bundles, 'categories': categories})

@anti_admin
def cart(request):
    cart = UserCart(request)
    products = cart.get_products
    quantities = cart.get_quantities
    # totals = cart.cart_total()
    return render(request, 'ecommerce/user/cart.html', {'products': products, 'quantities': quantities})

@anti_admin
def product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product:
        messages.error(request, 'Product not found.')
        return redirect('shop')
    elif product.is_deleted == True:
        messages.error(request, 'Product not found.')
        return redirect('shop')

    return render(request, 'ecommerce/user/product.html', {'product': product})

def add_to_cart(request):
    cart = UserCart(request)
    if request.POST.get('action') == 'post':
        product_id = str(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        product = get_object_or_404(Product, id=product_id)

        if product_id in cart.cart:
            response = JsonResponse({'error': 'Product already in your cart.'})
            messages.error(request, 'Product already in your cart.')
            return response
        else:
            # Save to session
            cart.add(product=product, quantity=product_qty)

            cart_quantity = cart.__len__()

            # response = JsonResponse({'Product Name: ': product.name})
            response = JsonResponse({'qty': cart_quantity})
            messages.success(request, ('Product added to cart.'))
            return response
    
def add_to_checkout_now(request):
    cart = UserCart(request)
    if request.POST.get('action') == 'post':
        product_id = request.POST.get('product_id')
        product_qty = int(request.POST.get('product_qty'))

        product = get_object_or_404(Product, id=product_id)
        # Save to session
        cart.add(product=product, quantity=product_qty)

        cart_quantity = cart.__len__()

        response = JsonResponse({'qty': cart_quantity})
        messages.success(request, ('Product added to cart.'))
        return response

def add_to_checkout_cart(request):
    if request.POST.get('action') == 'post':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')

        product = get_object_or_404(Product, id=product_id)
        user = get_object_or_404(User, id=request.user.id)

        existing_product = Cart.objects.filter(product=product, user=user).first()

        if existing_product:
            existing_product.quantity = quantity
            existing_product.save()
        else:
            Cart.objects.create(product=product, user=user, quantity=quantity)

        response = JsonResponse({'success': True})
        return response

def remove_from_checkout_cart(request):
    if request.POST.get('action') == 'post':
        product_id = request.POST.get('product_id')

        product = get_object_or_404(Product, id=product_id)
        user = get_object_or_404(User, id=request.user.id)

        product_to_delete = get_object_or_404(Cart, product=product, user=user)

        product_to_delete.delete()

        response = JsonResponse({'success': True})
        return response

    return JsonResponse({'error': 'Invalid Request'})

def update_cart(request):
    cart = UserCart(request)
    if request.POST.get('action') == 'post':
        product_id = str(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        product = get_object_or_404(Product, id=product_id)
        if request.user.is_authenticated:
            user = get_object_or_404(User, id=request.user.id)

            existing_product = Cart.objects.filter(product=product, user=user).first()

            if existing_product:
                existing_product.quantity = product_qty
                existing_product.save()

        cart.update(product=product_id, quantity=product_qty)

        response = JsonResponse({'qty': product_qty})
        return response
        
def delete_cart(request):
    cart = UserCart(request)
    if request.POST.get('action') == 'post':
        product_id = str(request.POST.get('product_id'))

        if request.user.is_authenticated:
            user = get_object_or_404(User, id=request.user.id)

            product_to_delete = Cart.objects.filter(product=product_id, user=user)
            if product_to_delete.exists():
                product_to_delete.delete()

        cart.delete(product=product_id)

        response = JsonResponse({'product': product_id})
        messages.success(request, ('Product removed from cart.'))
        return response
    
from django.views.decorators.csrf import csrf_exempt

# Disable greater than 30 orders in a day
@csrf_exempt
def get_order_counts(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)
    today = manila_time
    orders = Order.objects.filter(order_date__gte=today, is_deleted=False).values('order_date').annotate(order_count=Count('order_date'))
    order_counts = {order['order_date'].strftime('%Y-%m-%d'): order['order_count'] for order in orders}
    print(order_counts)
    return JsonResponse(order_counts)

# User Checkout
@login_required
@anti_admin
def checkout(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    cart = UserCart(request)
    user = get_object_or_404(User, id=request.user.id)
    items = Cart.objects.filter(user=user)



    if not items:
        messages.warning(request, 'Please select a product to checkout. Try to reselect products again.')
        return redirect('cart')
    
    for item in items:
        if item.product.stock == '0':
            messages.error(request, f'{item.product.type} {item.product.name} has no stock.')
            return redirect('cart')
    
    products = cart.get_guest_products()
    checked_out_products_ids = [product.id for product in products]

    if request.method == 'POST':
        print(request.POST)
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact_no = request.POST.get('contact_no')
        address = request.POST.get('address')
        pickup_date = request.POST.get('pickup_date')
        amount = request.POST.get('amount')
        points = request.POST.get('points')

        if user.points == 0:
            current_points = user.points
            subrated_points = int(current_points) - int(points)
            user.points = subrated_points
            user.save()

        user.points = round(int(amount) * 0.10)
        user.is_ordered = True
        user.save()

        order = Order.objects.create(name=name, user=user, email=email, contact_no=contact_no, address=address, pickup_date=pickup_date, amount=amount, order_date=manila_time)

        for index, product in enumerate(products, start=1):
            product_id = request.POST.get(f'product{index}')
            product_id = str(product_id)
            print(product_id)
            quantity = request.POST.get(f'quantity{index}')

            try:
                product_instance = Product.objects.get(id=product_id)
            except Exception as e:
                pass
            # product_instance = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(user=user, order=order, product=product_instance, quantity=quantity)
            # Subtract cart items into the Product Stock
            Product.objects.filter(id=product_id).update(stock=F('stock') - quantity)

        Cart.objects.filter(Q(user=user) & Q(product__id__in=checked_out_products_ids)).delete()
        cart.remove_checked_out_products(request, checked_out_products_ids)

        # Format Date
        order_date_formatted = order.order_date.date()
        time_formatted = order.order_date.time()

        subject = 'Order placed at Deeco Electronics.'

        message1 = f'Hi, {order.name}.'
        message2 = 'Your order has been placed.'
        message3 = f'Order ID: {order.id}'
        message4 = f'Placed At: {order_date_formatted} {time_formatted}'
        message5 = f'Pickup Date: {order.pickup_date}'
        message6 = f'Amount To Pay: ₱{order.amount}'
        order_status = f'Status: {order.status}'
        message7 = 'Thank you for shopping with us!'
        app_url = settings.APP_URL
        print(order)
        receiver = [order.email]
        # Send Email
        template = 'email.html'
        context = {
            'message1': message1,
            'message2': message2,
            'message3': message3,
            'message4': message4,
            'message5': message5,
            'message6': message6,
            'message7': message7,
            'order_status': order_status,
            'app_url': app_url
        }
        html_message = render_to_string(template, context)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = receiver
        send_mail(subject, '', from_email, to_email, html_message=html_message)

        messages.success(request, 'Order has been placed. Check your email for updates. Thank you for shopping!')
        return redirect('cart')
    
    return render(request, 'ecommerce/user/checkout.html', {'user': user, 'items': items})

@anti_admin
def guest_checkout(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    cart = UserCart(request)
    user = request.user
    products = cart.get_guest_products()
    checked_out_products_ids = [product.id for product in products]

    for product in checked_out_products_ids:
        lookup_product = Product.objects.get(id=product)
        if lookup_product.stock == '0':
            messages.error(request, f'{lookup_product.type} {lookup_product.name} has no stock')
            return redirect('cart')

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact_no = request.POST.get('contact_no')
        address = request.POST.get('address')
        pickup_date = request.POST.get('pickup_date')
        amount = request.POST.get('amount')

        order = Order.objects.create(name=name, email=email, contact_no=contact_no, address=address, pickup_date=pickup_date, order_date=manila_time, amount=amount)

        for index, product in enumerate(products, start=1):
            product_id = request.POST.get(f'product{index}')
            quantity = request.POST.get(f'quantity{index}')

            product_instance = Product.objects.get(id=product_id)
            OrderItem.objects.create(order=order, product=product_instance, quantity=quantity)

            Product.objects.filter(id=product_id).update(stock=F('stock') - quantity)

        cart.remove_checked_out_products(request, checked_out_products_ids)

        # Format Date
        order_date_formatted = order.order_date.date()
        time_formatted = order.order_date.time()

        subject = 'Order placed at Deeco Electronics.'

        message1 = f'Hi, {order.name}.'
        message2 = 'Your order has been placed.'
        message3 = f'Order ID: {order.id}'
        message4 = f'Placed At: {order_date_formatted} {time_formatted}'
        message5 = f'Pickup Date: {order.pickup_date}'
        message6 = f'Amount To Pay: ₱{order.amount}'
        order_status = f'Status: {order.status}'
        message7 = 'Thank you for shopping with us!'
        app_url = settings.APP_URL
        print(app_url)
        receiver = [order.email]
        # Send Email
        template = 'email.html'
        context = {
            'message1': message1,
            'message2': message2,
            'message3': message3,
            'message4': message4,
            'message5': message5,
            'message6': message6,
            'message7': message7,
            'order_status': order_status,
            'app_url': app_url
        }
        html_message = render_to_string(template, context)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = receiver
        send_mail(subject, '', from_email, to_email, html_message=html_message)

        messages.success(request, 'Order has been placed. Check your email for updates. Thank you for shopping!')
        return redirect('cart')
    
    context = {
        'user': user,
        'products': products,
    }
    return render(request, 'ecommerce/user/checkout.html', context)

# Marks is_delete to True when user cancel the order
@login_required
@anti_admin
def soft_delete_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order')
        order = get_object_or_404(Order, id=order_id)
        order_products = OrderItem.objects.filter(order=order)
        user = get_object_or_404(User, id=order.user.id)
        for product in order_products:
            product.product.stock = int(product.product.stock)
            product.product.stock += int(product.quantity)
            product.product.save()
            print(product)

        order.is_deleted = True
        order.status = 'Cancelled'
        current_points = user.points
        order_points = round(int(order.amount) * 0.10)
        subrated_points = int(current_points) - order_points
        user.points = subrated_points
        user.save()
        order.save()

        messages.success(request, f'Order {order.id} cancelled. Shop again!')
        return redirect('profile')

def search_products(request):
    print("Received AJAX request")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        print("Detected AJAX request")
        product_name = request.GET.get('product_name', '')

        # Check if product name that user inputted has a value
        if product_name:
            print("Filtering products with name:", product_name)

            filtered_products = Product.objects.filter(Q(name__icontains=product_name) & Q(type='Product')).exclude(stock=0)

            # product_cards_html = render_to_string('product-card.html', {'products': filtered_products})
            # print(filtered_products)
            # return HttpResponse(product_cards_html)
        # If none, get all products
        else:
            print("Filtering products with name:", product_name)

            filtered_products = Product.objects.filter(type='Product')

        product_cards_html = render_to_string('product-card.html', {'products': filtered_products})

        return HttpResponse(product_cards_html)
        
    print("Invalid AJAX request")
    
    return JsonResponse({'error': 'Invalid request'})

def search_bundles(request):
    print("Received AJAX request")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        print("Detected AJAX request")
        product_name = request.GET.get('product_name', '')

        # Check if product name that user inputted has a value
        if product_name:
            print("Filtering products with name:", product_name)

            filtered_products = Product.objects.filter(Q(name__icontains=product_name) & Q(type='Bundle')).exclude(stock=0)

            product_cards_html = render_to_string('bundle-card.html', {'bundles': filtered_products})
            print(filtered_products)
            return HttpResponse(product_cards_html)
        # If none, get all products
        else:
            print("Filtering products with name:", product_name)

            filtered_products = Product.objects.filter(type='Bundle')
            
            product_cards_html = render_to_string('bundle-card.html', {'bundles': filtered_products})

            return HttpResponse(product_cards_html)
        
    print("Invalid AJAX request")
    
    return JsonResponse({'error': 'Invalid request'})

# Send Email Function
def custom_email(subject, message, recipient_list, from_email, from_name):
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            from_name
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
# Admin CRUD
def delete_product(request, product_id):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    product = get_object_or_404(Product, id=product_id)

    product.is_deleted = True
    product.save()

    if product.type == 'Bundle':
        ActivityLog.objects.create(user=request.user, activity=f'Deleted Bundle {product.id}', timestamp=manila_time)
        messages.success(request, f'Bundle {product.id} has been deleted.')
        return redirect('bundle_list')
    else:
        ActivityLog.objects.create(user=request.user, activity=f'Deleted Product {product.id}', timestamp=manila_time)
        messages.success(request, f'Product {product.id} has been deleted.')
        return redirect('product_list')

# Forgot Password
def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)

                token = default_token_generator.make_token(user)
                print(token)
                
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                token_encoded = urlsafe_base64_encode(force_bytes(token))

                # Convert the +00:00 to +08:00(UTC to Asia/Manila)
                utc_time = timezone.now()

                manila_tz = pytz.timezone('Asia/Manila')

                manila_time = utc_time.astimezone(manila_tz)
                # Save the token to User
                user.password_reset_token = token_encoded
                user.password_reset_token_created_at = manila_time
                user.save()

                reset_link = f'http://127.0.0.1:8000/reset-password/{uidb64}/{token_encoded}'

                subject = 'Forgot Password at Deeco Electronics'
                app_url = settings.APP_URL
                message1 = f'Hi, {user.name}.'
                message2 = 'You requested to change your password.'
                message3 = 'Click this link to change your password.'
                message4 = reset_link
                message5 = ''
                message6 = ''
                order_status = ''
                message7 = ''
                receiver = [user.email]
                # Send Email
                template = 'forgot-password-email.html'
                context = {
                    'message1': message1,
                    'message2': message2,
                    'message3': message3,
                    'message4': message4,
                    'message5': message5,
                    'message6': message6,
                    'message7': message7,
                    'order_status': order_status,
                    'app_url': app_url
                }
                html_message = render_to_string(template, context)
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = receiver
                send_mail(subject, '', from_email, to_email, html_message=html_message)

                messages.success(request, 'Password Reset Link has been sent to your email.')
                return redirect('forgot_password')
            except User.DoesNotExist:
                messages.error(request, 'User with the email you submitted does not exist.')
                return redirect('forgot_password')
        else:
            print(form.errors)
    else:
        form = ForgotPasswordForm()
        
    return render(request, 'ecommerce/auth/forgot-password.html', {'form': form})

def reset_password(request, uidb64, token):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    try:
        user_id = urlsafe_base64_decode(uidb64).decode('utf-8')
        user = User.objects.get(pk=user_id)

        if user.password_reset_token != token or (manila_time - user.password_reset_token_created_at) > timedelta(hours=1):
            messages.error(request, 'Invalid or expired reset link.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            new_password = request.POST['password1']
            confirm_password = request.POST['password2']

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()

                # update_session_auth_hash(request, user)

                messages.success(request, 'Password reset successful. Log in with your new password.')
                return redirect('login')
            else:
                messages.error(request, 'Password do not match.')
                return redirect('reset_password', uidb64=uidb64, token=token)
    except (User.DoesNotExist, UnicodeDecodeError, ValueError):
        messages.error(request, 'Invalid reset link. User not found.')
        return redirect('login_view')
    
    return render(request, 'ecommerce/auth/reset-password.html', {'uidb64': uidb64, 'token': token, 'user': user})

# User Reviews
def submit_review(request):
    # Convert the +00:00 to +08:00(UTC to Asia/Manila)
    utc_time = timezone.now()

    manila_tz = pytz.timezone('Asia/Manila')

    manila_time = utc_time.astimezone(manila_tz)

    user = get_object_or_404(User, id=request.user.id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comments = request.POST.get('comments')

        Review.objects.create(user=user, rating=rating, comments=comments, timestamp=manila_time)
        user.is_ordered = False
        user.save()

        messages.success(request, 'We got your feedback! Thank you for shopping with us.')
        return redirect('shop')
    else:
        messages.error(request, 'Invalid request.')
        return redirect('shop')

@login_required
@anti_admin
def remove_review(request):
    if request.method == 'POST':
        user = get_object_or_404(User, id=request.user.id)

        if user.is_ordered == True:
            user.is_ordered=False
            user.save()
            
            return JsonResponse({'status': 'success', 'message': 'Review removed successfully'})
        
def custom_404_view(request, exception):
    return render(request, '404.html', {}, status=404)

def custom_500_view(request):
    return render(request, '500.html', {}, status=500)