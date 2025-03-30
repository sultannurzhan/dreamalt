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


class AddPostView(LoginRequiredMixin, View):
    def post(self, request, pk):
        group = get_object_or_404(Group, id=pk)
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            if post.body != "" or request.FILES.get('image'):
                post.user = request.user
                post.group = group
                post.image = request.FILES.get('image')
                post.save()
        return redirect('group', pk=pk)


def getPosts(request):
    group_posts = Post.objects.all()
    if request.user.is_authenticated:
        current_user = UserProfile.objects.get(user=request.user)
        my_following = current_user.following.all()
        arr = []
        for follower in my_following:
            arr.append(follower.username)
        feed_posts = Post.objects.filter(
                                        Q(user__username__in=arr)
        )
    else:
        feed_posts = group_posts

    feed_posts_json = feed_posts.values('body', 'user__username', 'group', 'user__profile__profile_pic', 'created')
    return JsonResponse({"feed_posts":list(feed_posts_json)})


@login_required(login_url='login')
def deletePost(request, pk):
    post = Post.objects.get(id=pk)
    if request.user != post.user:
        return JsonResponse({'error': 'You are not allowed to delete'})
       
    if request.method == "POST":
        if post.image and post.image.name and os.path.isfile(post.image.path):
            os.remove(post.image.path)
        post.delete()
        return JsonResponse({'success': 'Post deleted successfully'})
    print(request.method)
    return JsonResponse({'error': 'Invalid request method'})


@login_required(login_url="login")
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    likes_count = post.like_set.count()
    liked = True if like.pk else False

    return JsonResponse({'likes_count': likes_count, 'liked': liked})