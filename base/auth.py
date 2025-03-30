from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from .forms import RegisterUserForm
class LoginUser(View):
    def get(self, request):
        page = 'login'
        if request.user.is_authenticated:
            return redirect('home')
        context = {'page':page}
        return render(request, 'base/login_register.html', context)

    def post(self, request):
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is None:
            messages.error(request, 'Username or Password is incorrect')
            return redirect('login')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or Password is incorrect')
            return redirect('login')

def logoutUser(request):
    logout(request)
    return redirect('login')

class RegisterUser(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = RegisterUserForm()
        return render(request, 'base/login_register.html', {'form' : form})

    @csrf_exempt
    def post(self, request):
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit = False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Error occured during registration')
            form = RegisterUserForm()
            return render(request, 'base/login_register.html', {'form' : form})