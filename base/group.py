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


class GroupDetails(View):
    def get(self, request, pk):

        q = request.GET.get('q') if request.GET.get('q') != None else ''
        search_query = request.GET.get('q', '')
        if search_query.startswith('@'):
            username_query = search_query[1:]
        else:
            username_query = search_query

        self.group = Group.objects.get(id=pk)
        group_posts = self.group.post_set.all()
        participants = self.group.participants.all().order_by('-username')

        group_posts = self.group.post_set.all()

        group_posts = group_posts.filter(
            Q(group__topic__title__icontains=search_query) |
            Q(body__icontains=search_query) |
            Q(user__username__icontains=username_query) |
            Q(user__first_name__icontains=username_query) |
            Q(user__last_name__icontains=username_query)
        )

        for post in group_posts:
            post.likes_count = post.like_set.count()

        is_following = request.user in self.group.participants.all()

        context = {
            'group': self.group, 
            'group_posts': group_posts, 
            'participants': participants, 
            'is_authenticated': request.user.is_authenticated,
            'is_following': is_following,
        }
        return render(request, 'base/group.html', context)



class FollowGroup(View):
    def post(self, request, pk):
        group = get_object_or_404(Group, id=pk)
        if request.user.is_authenticated:
            group.participants.add(request.user)
            request.user.profile.followed_groups.add(group)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})


class UnfollowGroup(View):
    def post(self, request, pk):
        group = get_object_or_404(Group, id=pk)
        if request.user.is_authenticated:
            group.participants.remove(request.user)
            request.user.profile.followed_groups.remove(group)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})




class CreateGroupView(LoginRequiredMixin, View):
    login_url = 'login'
    
    def get(self, request):
        topics = Topic.objects.all()
        form = GroupForm()
        context = {'form': form, 'topics': topics}
        return render(request, 'base/create_group_form.html', context)

    def post(self, request):
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if the uploaded image size exceeds the limit
            if request.FILES.get('image') and request.FILES['image'].size > 10 * 1024 * 1024:
                return JsonResponse({'error': 'Image too big'})

            group = form.save(commit=False)
            group.host = request.user
            topic_name = request.POST.get('topic', '').strip()
            if topic_name:
                topic, created = Topic.objects.get_or_create(title__iexact=topic_name, defaults={'title': topic_name})
                group.topic = topic
            if request.FILES.get('image') is None:
                group.image = 'group-image.png'
            else:
                group.image = request.FILES.get('image')
            group.save()
            group.participants.add(request.user)
            current_user = UserProfile.objects.get(user=request.user)
            current_user.owned_groups.add(group)
            current_user.followed_groups.add(group)
            
            return redirect('group', pk=group.id)

        print("⚠️ Group form is invalid:", form.errors)
        topics = Topic.objects.all()
        context = {'form': form, 'topics': topics}
        return render(request, 'base/create_group_form.html', context)
    

@require_GET
def suggest_topics(request):
    query = request.GET.get('term', '')
    try:
        if query:
            suggestions = Topic.objects.filter(title__icontains=query) \
                                       .annotate(group_count=Count('group')) \
                                       .order_by('-group_count') \
                                       .values_list('title', flat=True)[:10]
            return JsonResponse(list(suggestions), safe=False)
        return JsonResponse([], safe=False)
    except Exception as e:
        import traceback
        print("🔥 suggest_topics error:", e)
        traceback.print_exc()
        return JsonResponse([], safe=False, status=500)


class UpdateGroupView(LoginRequiredMixin, View):
    login_url = 'login'

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=kwargs['group_id'])
        if self.group.host != request.user:
            return HttpResponse('You are not allowed to update')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, group_id):
        form = GroupForm(instance=self.group)
        return render(request, 'base/update_group_form.html', {'group': self.group, 'form': form})

    def post(self, request, group_id):
        form = GroupForm(request.POST or None, request.FILES or None, instance=self.group)
        old_image = self.group.image

        if form.is_valid():
            group = form.save(commit=False)
            topic_name = request.POST.get('topic', '').strip()
            if topic_name:
                topic, created = Topic.objects.get_or_create(title__iexact=topic_name, defaults={'title': topic_name})
                group.topic = topic
            group.image = request.FILES.get('image')
            if 'clear_image' in request.POST:
                if os.path.isfile(old_image.path) and old_image != "group-image.png":
                    os.remove(old_image.path)
                group.image = 'group-image.png'
            elif group.image in ["", None]:
                group.image = old_image
            group.save()
            return redirect('group', group.id)

        return render(request, 'base/update_group_form.html', {'group': self.group, 'form': form})


@login_required(login_url='login')
def deleteGroup(request, pk):
    group = Group.objects.get(id=pk)
    
    if group.image != "group-image.png":
        old_image = group.image
    else:
        old_image = None
    
    if request.user != group.host:
        return HttpResponse('You are not allowed to delete')

    if request.method == "POST":
        group.delete()
        if old_image:
            if old_image != 'group-image.png':
                old_image.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj':group})
