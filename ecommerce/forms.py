import re
from django import forms
from .models import *
from django.contrib.auth.forms import PasswordChangeForm

class RegisterForm(forms.Form):
    name                        = forms.CharField(label='Name', max_length=100, required=True, error_messages={'required': 'Complete Name is required.'})
    email                       = forms.EmailField(label='Email', required=True, error_messages={'required': "Email Address is required."})
    contact_no                  = forms.CharField(label='Contact Number', max_length=11, required=True, error_messages={'required': "Contact Number is required."})
    address                     = forms.CharField(label='Address', required=True, error_messages={'required': 'Complete Address is required.'})
    password                    = forms.CharField(label='Password', widget=forms.PasswordInput)
    confirm_password            = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    user_type                   = forms.CharField(label='User Type')

    def clean_contact_no(self):
        contact_no = self.cleaned_data['contact_no']
        if len(contact_no) != 11:
            raise forms.ValidationError("Contact Number is invalid.")
        return contact_no

    def clean_email(self):
        email = self.cleaned_data['email']

        if '.' not in email.split('@')[-1]:
            raise forms.ValidationError("Email Address is required.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('password_confirmation')

        if len(password) < 8:
            raise forms.ValidationError("Password must have 8 or more characters.")

        if not any(char.isupper() for char in password):
            raise forms.ValidationError("Password must contain at least 1 uppercase letter.")

        if not any(char.islower() for char in password):
            raise forms.ValidationError("Password must contain at least 1 lowercase letter.")

        if not any(char.isdigit() for char in password):
            raise forms.ValidationError("Password must contain at least 1 number.")

        special_characters = "~!@#$%^&*()_+{}|:\"<>?`-=[]\\;',./"
        if not any(char in special_characters for char in password):
            raise forms.ValidationError("Password must contain at least 1 special character.")

        # if password != password_confirmation:
        #     raise forms.ValidationError("Password do not match.")
        return password

    class Meta:
        model = User
        fields = ['name', 'email', 'contact_no', 'password1', 'password2', 'user_type']

class LoginForm(forms.Form):
    email = forms.CharField(label='Email Address', required=True)
    password = forms.CharField(label='Password', required=True)

    # class Meta:
    #     model = User
    #     fields = ['email', 'password']

class AdminRegisterForm(forms.Form):
    name                        = forms.CharField(label='Name', max_length=100)
    email                       = forms.EmailField(label='Email', required=True, error_messages={'required': "Email Address is required."})
    password                    = forms.CharField(label='Password', widget=forms.PasswordInput)
    confirm_password            = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email']

        if '.' not in email.split('@')[-1]:
            raise forms.ValidationError("Email Address is required.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('password_confirmation')

        if len(password) < 8:
            raise forms.ValidationError("Password must have 8 or more characters.")

        if not any(char.isupper() for char in password):
            raise forms.ValidationError("Password must contain at least 1 uppercase letter.")

        if not any(char.islower() for char in password):
            raise forms.ValidationError("Password must contain at least 1 lowercase letter.")

        if not any(char.isdigit() for char in password):
            raise forms.ValidationError("Password must contain at least 1 number.")

        special_characters = "~!@#$%^&*()_+{}|:\"<>?`-=[]\\;',./"
        if not any(char in special_characters for char in password):
            raise forms.ValidationError("Password must contain at least 1 special character.")

        # if password != password_confirmation:
        #     raise forms.ValidationError("Password do not match.")
        return password

    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2'] 

class PasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Old Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Old Password'})
    )
    new_password1 = forms.CharField(
        label="New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter New Password'}),
        help_text="Your password must be at least 8 characters long, and contain at least one number and one letter."
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'})
    )

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if len(password1) < 8:
            raise forms.ValidationError("The new password must be at least 8 characters long.")
        return password1

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two new password fields didn't match.")
        return password2       

class ProductForm(forms.ModelForm):
    name = forms.CharField(label='Name', max_length=100)
    description = forms.CharField(label='Description', max_length=255)
    price = forms.CharField(label='Price', max_length=255)
    stock = forms.CharField(label='Stock', max_length=100)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), label='Category')
    image1 = forms.ImageField(label='image1')
    image2 = forms.ImageField(label='image2', required=False)
    image3 = forms.ImageField(label='image3', required=False)
    image4 = forms.ImageField(label='image4', required=False)
    image5 = forms.ImageField(label='image5', required=False)
    image6 = forms.ImageField(label='image6', required=False)

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6']

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()
