from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import UserRegisterForm

'''
    Login page view

    Returns simple login page
'''

# Create your views here.
def login(request):
    return render( request, 'users/login.html', {})

'''
    Register view for user registeration

    Redirects to login page

'''
def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success( request, "Account has been created for {}".format(username))

            return redirect( 'home' )

    else:
        form = UserRegisterForm()

    return render( request, 'users/register.html', {'form':form} )

'''
    The handler for the AJAX request

    Checks whether the inputted username is takend or not

    Returns a JSON object that includes a boolean for availability 
'''
def check(request):
    username = request.GET.get('username')
    available = False if User.objects.get(username=username) else True
    data = {
        'available': available
    }
    return JsonResponse(data)
