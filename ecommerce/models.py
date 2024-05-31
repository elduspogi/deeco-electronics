from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils import timezone
import uuid
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from django.utils.text import slugify
import datetime
import os

# Create your models here.
class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("You have not provided a valid email address.")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    name = models.CharField(max_length=255, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    old_cart = models.CharField(max_length=255, null=True, blank=True)
    is_banned = models.BooleanField(default=False)
    points = models.CharField(max_length=255, default=0, null=True, blank=True)
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_token_created_at = models.DateTimeField(blank=True, null=True)
    is_ordered = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{ self.id } - { self.email }"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=50)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, default='', blank=True, null=True)
    price = models.CharField(max_length=255)
    stock = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    image1 = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image3 = models.ImageField(upload_to='products/', null=True, blank=True)
    image4 = models.ImageField(upload_to='products/', null=True, blank=True)
    image5 = models.ImageField(upload_to='products/', null=True, blank=True)
    image6 = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    type = models.CharField(max_length=100, default='Product')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
        super().save(*args, **kwargs)
        # else:
        #     old_instance = Product.objects.get(pk=self.pk)
        #     old_images = {
        #         'image1': old_instance.image1.path if old_instance.image1 else None,
        #         'image2': old_instance.image2.path if old_instance.image2 else None,
        #         'image3': old_instance.image3.path if old_instance.image3 else None,
        #         'image4': old_instance.image4.path if old_instance.image4 else None,
        #         'image5': old_instance.image5.path if old_instance.image5 else None,
        #         'image6': old_instance.image6.path if old_instance.image6 else None,
        #     }


        # def resize_image(image_field):
        #     if image_field and image_field.name:
        #         img = Image.open(image_field)
        #         img = img.convert('RGB')  

        #         # Crop the image from the center
        #         # width, height = img.size
        #         # min_dim = min(width, height)
        #         # left = (width - min_dim) / 2
        #         # top = (height - min_dim) / 2
        #         # right = (width + min_dim) / 2
        #         # bottom = (height + min_dim) / 2
        #         # img = img.crop((left, top, right, bottom))

        #         img = img.resize((800, 600), Image.LANCZOS)

        #         # Generate a new filename for the resized image
        #         filename, extension = os.path.splitext(image_field.name)
        #         new_filename = f"{filename}_resized{extension}"

        #         # Save the resized image to BytesIO
        #         img_io = BytesIO()
        #         img.save(img_io, format='JPEG', quality=85)
        #         img_content = ContentFile(img_io.getvalue(), name=image_field.name)

        #         print(image_field.path)
        #         if os.path.exists(image_field.path):
        #             # os.remove(image_field.path)
        #             pass

        #         # Update the image field with the resized image
        #         # image_field.save(image_field.name, img_content, save=False)
        #         image_field.save(new_filename, img_content, save=False)

        # resize_image(self.image1)
        # resize_image(self.image2)
        # resize_image(self.image3)
        # resize_image(self.image4)
        # resize_image(self.image5)
        # resize_image(self.image6)

        # super().save(*args, **kwargs)

class Cart(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return self.id

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
        super().save(*args, **kwargs)

class Order(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    contact_no = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(max_length=255, null=True, blank=True)
    amount = models.CharField(max_length=255)
    # order_date = models.DateTimeField(auto_now_add=True)
    # order_date = models.DateTimeField(default=timezone.now)
    order_date = models.DateTimeField(null=True, blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    # Pending, To Pack, Ready For Pick Up, Picked Up, Cancelled
    status = models.CharField(max_length=100, default='Pending')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Order - {self.id} - {self.name} - {self.user}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.CharField(max_length=100, default=1,null=True, blank=True)

    def __str__(self):
        return f'Order Item - {self.order} - {self.user}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
        super().save(*args, **kwargs)

class ActivityLog(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    activity = models.CharField(max_length=1000, null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.id} - {self.user.name} - {self.activity}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
        super().save(*args, **kwargs)

class Review(models.Model):
    id = models.CharField(max_length=26, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    rating = models.CharField(max_length=10, null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.id} - {self.user.name} - {self.rating}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex.replace('-', '')[:26].upper()
        super().save(*args, **kwargs)