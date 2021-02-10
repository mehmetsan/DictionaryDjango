from django.core.exceptions import PermissionDenied
from dictword.models import Dictword
from django.shortcuts import redirect

'''
    Decorator for practice page.

    Checks whether the User is authenticated

    If User is logged in, and has words > 9, returns the view function

    Else redirects to the landing page  
'''
def user_see_practice(function):
    def wrap(request, *args, **kwargs):
        user = request.user

        if user.is_authenticated:
            
            user_words = Dictword.objects.all().filter(user=user)
            practice = True if len(user_words) > 9 else False

            if practice:
                return function(request, *args, **kwargs)

        return redirect('/')

    
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap