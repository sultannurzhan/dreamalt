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


class BaseUserView(View):
    def get_user_context(self, user):
        userdetails = UserProfile.objects.get(user=user)
        topics = Topic.objects.all()
        groups = user.group_set.all()
        group_posts = user.post_set.all()
        followers = userdetails.followers.all()
        following = userdetails.following.all()
        owned_groups = userdetails.owned_groups.all()
        followed_groups = userdetails.followed_groups.all()

        return {
            'user': user,
            'topics': topics,
            'groups': groups,
            'group_posts': group_posts,
            'followers': followers,
            'following': following,
            'owned_groups': owned_groups,
            'followed_groups': followed_groups
        }


class UserProfileView(BaseUserView):
    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        context = self.get_user_context(user)
        if request.user.is_authenticated:
            mydetails = UserProfile.objects.get(user=request.user)
            myfollowers = mydetails.followers.all()
            myfollowing = mydetails.following.all()
            context['myfollowers'] = myfollowers
            context['myfollowing'] = myfollowing

        ifollowed = False
        for i in range(len(context['followers'])):
            if (context['followers'][i] == request.user):
                ifollowed = True
                break

        context['ifollowed'] = ifollowed
        return render(request, 'base/profile-pages/profile.html', context)

    def post(self, request, pk):
        user = get_object_or_404(User, id=pk)
        userdetails = UserProfile.objects.get(user=user)
        mydetails = UserProfile.objects.get(user=request.user)
        followers = userdetails.followers.all()

        ifollowed = False
        for i in range(len(followers)):
            if (followers[i] == request.user):
                ifollowed = True
                break

        if ifollowed == False:
            userdetails.followers.add(request.user)
            mydetails.following.add(user)
        elif ifollowed == True:
            userdetails.followers.remove(request.user)
            mydetails.following.remove(user)

        return HttpResponseRedirect(request.path_info)


class UserGroups(BaseUserView):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        context = self.get_user_context(user)
        
        q = request.GET.get('q') if request.GET.get('q') is not None else ''

        if q == 'owned-groups':
            context['groups'] = context['owned_groups'].annotate(num_posts=Count('post')).order_by('-num_posts')
        else:
            context['groups'] = context['followed_groups'].annotate(num_posts=Count('post')).order_by('-num_posts')

        if not q:
            context['groups'] = context['followed_groups'].annotate(num_posts=Count('post')).order_by('-num_posts')

        return render(request, 'base/profile-pages/owned-groups.html', context)


class Followers(BaseUserView):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        context = self.get_user_context(user)
        if request.user.is_authenticated:
            mydetails = UserProfile.objects.get(user=request.user)
            myfollowers = mydetails.followers.all()
            myfollowing = mydetails.following.all()
            context['myfollowers'] = myfollowers
            context['myfollowing'] = myfollowing

        return render(request, 'base/profile-pages/followers.html', context)


class Following(BaseUserView):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        context = self.get_user_context(user)

        return render(request, 'base/profile-pages/following.html', context)


class UpdateUserView(LoginRequiredMixin, View):
    login_url = '/login/'
    #redirect_field_name = 'redirect_to'
    def get(self, request):
        profile = UserProfile.objects.get(user=request.user.id)
        form = UserForm(instance=request.user)
        form2 = UserForm2(instance=request.user.profile)

        old_profile_pic = profile.profile_pic
        print(old_profile_pic)
     
        context = {'form': form, 'form2': form2, 'profile': profile}
        return render(request, 'base/update_user.html', context)

    @transaction.atomic
    def post(self, request):
        profile = UserProfile.objects.get(user=request.user.id)
        
        old_profile_pic = profile.profile_pic
        print(old_profile_pic)

        form = UserForm(request.POST, instance=request.user)
        form2 = UserForm2(request.POST or None, request.FILES or None, instance=request.user.profile)

        if form.is_valid() and form2.is_valid():
            profile2 = form2.save(commit=False)
            profile2.profile_pic = request.FILES.get('profile_pic')
            if 'clear_image' in request.POST:
                if old_profile_pic and os.path.isfile(old_profile_pic.path) and old_profile_pic!="noprofile.webp":
                    os.remove(old_profile_pic.path)
                profile2.profile_pic = "noprofile.webp"
            elif not request.FILES.get('profile_pic'):
                profile2.profile_pic = old_profile_pic if old_profile_pic else "noprofile.webp"
            else:
                profile2.profile_pic = request.FILES.get('profile_pic')

            form.save()
            profile2.save()

            return redirect('user-profile', pk=request.user.id)

        context = {'form': form, 'form2': form2, 'profile': profile}
        return render(request, 'base/update_user.html', context)
