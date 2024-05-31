from django.shortcuts import redirect

def anti_user(function):
    def wrapper(request, *args, **kwargs):
        if request.user.user_type == 'User':
            return redirect('index')
        return function(request, *args, **kwargs)
    return wrapper

def anti_admin(function):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            pass        
        elif request.user.user_type == 'Admin' or request.user.user_type == 'Superadmin':
            return redirect('dashboard')
        return function(request, *args, **kwargs)
    return wrapper

def for_superadmin(function):
    def wrapper(request, *args, **kwargs):
        if request.user.user_type == 'Admin':
            return redirect('dashboard')
        elif request.user.user_type == 'User':
            return redirect('index')
        
        return function(request, *args, **kwargs)
    return wrapper