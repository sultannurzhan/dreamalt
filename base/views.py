from datetime import datetime, timezone
from itertools import chain
from pydoc import describe
from tkinter import EW
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import *
from .forms import *
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.files.base import ContentFile
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator

def handler404(request, exception):
    return render(request, '404.html', status=404)
    
def handler500(request):
    return render(request, '500.html', status=500)


class GroupPage(View):
    def get(self, request):

        q = request.GET.get('q') if request.GET.get('q') != None else ''
        search_query = request.GET.get('q', '')
        if search_query.startswith('@'):
            username_query = search_query[1:]
        else:
            username_query = search_query

        sort = request.GET.get('sort')

        groups = Group.objects.filter(
            Q(topic__title__icontains=q) |
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(host__username__icontains=username_query) |
            Q(host__first_name__icontains=username_query) |
            Q(host__last_name__icontains=username_query)
        ).annotate(num_participants=Count('participants')).order_by('-num_participants')

        if sort == "most_participants":
            groups = groups.annotate(num_participants=Count('participants')).order_by('-num_participants')
        elif sort == "less_participants":
            groups = groups.annotate(num_participants=Count('participants')).order_by('num_participants')

        topics = Topic.objects.all()
        group_count = groups.count()
        group_posts = Post.objects.filter(Q(group__topic__title__icontains=q))

        context = {'groups': groups,
                    'topics': topics,
                    'group_count': group_count,
                    'group_posts': group_posts,
                    'sort': sort,
                    }

        return render(request, 'base/group_page.html', context)



class AboutView(View):
    def get(self, request):
        return render(request, 'company/about.html')

def careers(request):
    return render(request, 'default/uncomplete.html')

def terms(request):
    return render(request, 'default/uncomplete.html')

def privacy(request):
    return render(request, 'default/uncomplete.html')

def business(request):
    return render(request, 'default/uncomplete.html')

def contact(request):
    return render(request, 'default/uncomplete.html')

def yourAdChoices(request):
    return render(request, 'default/uncomplete.html')


class FollowingNewsView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):

        q = request.GET.get('q') if request.GET.get('q') != None else ''
        search_query = request.GET.get('q', '')
        if search_query.startswith('@'):
            username_query = search_query[1:]
        else:
            username_query = search_query

        followed_groups = UserProfile.objects.get(user=request.user).followed_groups.all()
        owned_groups = UserProfile.objects.get(user=request.user).owned_groups.all()

        posts = Post.objects.filter(
            Q(group__in=followed_groups)|
            Q(group__in=owned_groups)
        ).exclude(user=request.user)

        posts = posts.filter(
                Q(group__topic__title__icontains=search_query) |
                Q(body__icontains=search_query) |
                Q(user__username__icontains=username_query) |
                Q(user__first_name__icontains=username_query) |
                Q(user__last_name__icontains=username_query)
        )

        for post in posts:
            post.likes_count = post.like_set.count()

        topics = Topic.objects.all() \
            .annotate(num_groups=Count('group')) \
            .order_by('-num_groups')

        context = {'posts': posts, 'topics': topics}
        
        return render(request, 'base/following-news.html', context)




def login_required_ajax_view(request):
    if request.is_ajax():
        user_authenticated = request.user.is_authenticated
        if user_authenticated:
            return JsonResponse(data={'logged_in': True})
        return JsonResponse(data={'logged_in': False})
    return HttpResponse("not ajax")