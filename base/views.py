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
from .models import Group, Like, Topic, Post, UserProfile, ChatMessage, Comment
from .forms import GroupForm, RegisterUserForm, UserForm, UserForm2, PostForm, ChatMessageForm
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.files.base import ContentFile
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from django.db.models.functions import Random


def handler404(request, exception):
    return render(request, '404.html', status=404)
    
def handler500(request):
    return render(request, '500.html', status=500)

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

class Home(View):
    def get(self, request):
        q = request.GET.get('q') if request.GET.get('q') != None else ''
        
        # Get the search query from the user
        search_query = request.GET.get('q', '')

        # Check if the search query starts with "@"
        if search_query.startswith('@'):
            # Remove the "@" symbol from the search query
            username_query = search_query[1:]
        else:
            username_query = search_query

        if request.user.is_authenticated:
            groups = Group.objects.filter(
                Q(topic__title__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(host__username__icontains=username_query) |
                Q(host__first_name__icontains=username_query) |
                Q(host__last_name__icontains=username_query)
            ).annotate(random=Random()).order_by(
                Case(
                    When(host=request.user, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                'host__username',
                'random'
            )

            """
            annotate(num_posts=Count('post')).order_by(
                Case(
                    When(host=request.user, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                'host__username',
                '-num_posts'
            )
            """

        else:
            groups = Group.objects.filter(
                Q(topic__title__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(host__username__icontains=username_query) |
                Q(host__first_name__icontains=username_query) |
                Q(host__last_name__icontains=username_query)
            ).annotate(random=Random()).order_by('random')

        topics = Topic.objects.all() \
                    .annotate(num_groups=Count('group')) \
                    .order_by('-num_groups')

        group_count = groups.count()
        group_posts = Post.objects.filter(
            Q(group__topic__title__icontains=search_query) |
            Q(body__icontains=search_query) |
            Q(user__username=username_query) |
            Q(user__first_name__icontains=username_query) |
            Q(user__last_name__icontains=username_query)
        )

        if request.user.is_authenticated:            
            feed_posts = group_posts.exclude(user=request.user).annotate(random=Random()).order_by('random')
            if (len(feed_posts)==0):
                feed_posts = group_posts
        else:
            feed_posts = group_posts.annotate(random=Random()).order_by('random')

        context = {'groups': groups,
                    'topics': topics,
                    'group_count': group_count,
                    'group_posts': group_posts,
                    'feed_posts': feed_posts,
                
                    }
        return render(request, 'base/home.html', context)

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

    def post(self, request, pk):
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            if post.body!="":
                post.user = request.user
                self.group = Group.objects.get(id=pk)
                post.group = self.group
                post.save()
            return redirect('group', pk=pk)


def groupComments(request, pk, post_id):
    post = Post.objects.get(id=post_id)
    comments = post.comment_set.all()
    comment_list = []
    for comment in comments:
        full_name = comment.user.first_name + " " + comment.user.last_name
        comment_data = {
            'id': comment.id,
            'body': comment.body,
            'user': comment.user.username,
            'full_name': full_name,
            'profile_pic': comment.user.profile.profile_pic.url,
            'created': comment.created,
            'user_id': comment.user.id,
        }
        comment_list.append(comment_data)
    return JsonResponse({'comments': comment_list})

def addComment(request, pk, post_id):
    if request.method == 'POST':
        post = Post.objects.get(id=post_id)
        group = Group.objects.get(id=pk)
        comment_body = request.POST.get('comment-body')
        comment = Comment.objects.create(group=group, post=post, user=request.user, body=comment_body)
        comment_data = {
            'id': comment.id,
            'full_name': comment.user.get_full_name(),
            'body': comment.body,
            'created': comment.created,
            'user_id': comment.user.id,
        }
        return JsonResponse(comment_data)
    else:
        return HttpResponseNotAllowed(['POST'])

def deleteComment(request, commentId):
    if request.method == 'POST' and request.is_ajax():
        try:
            comment = Comment.objects.get(id=commentId)
            if comment.user == request.user:
                comment.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Not authorized.'})
        except Comment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Comment does not exist.'})
    else:
        return HttpResponseNotAllowed(['POST'])



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


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def login_required_ajax_view(request):
    if request.is_ajax():
        user_authenticated = request.user.is_authenticated
        if user_authenticated:
            return JsonResponse(data={'logged_in': True})
        return JsonResponse(data={'logged_in': False})
    return HttpResponse("not ajax")

@login_required(login_url="login")
def like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    likes_count = post.like_set.count()
    liked = True if like.pk else False

    return JsonResponse({'likes_count': likes_count, 'liked': liked})


class UserProfileView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        userdetails = UserProfile.objects.get(user=user)
        if request.user.is_authenticated:
            mydetails = UserProfile.objects.get(user=request.user)
            myfollowers = mydetails.followers.all()
            myfollowing = mydetails.following.all()

        topics = Topic.objects.all()
        groups = user.group_set.all()
        group_posts = user.post_set.all()

        followers = userdetails.followers.all()
        following = userdetails.following.all()
        owned_groups = userdetails.owned_groups.all()
        followed_groups = userdetails.followed_groups.all()
        #all_groups = list(chain(owned_groups, followed_groups))
        all_groups = followed_groups

        ifollowed = False

        for i in range(len(followers)):
            if (followers[i] == request.user):
                ifollowed = True
                break

        context = {'user': user, 'topics': topics, 'groups': groups, 'group_posts': group_posts, 'followers': followers, 'following': following, 'ifollowed': ifollowed, 'owned_groups': owned_groups, 'all_groups': all_groups}
        if request.user.is_authenticated:
            context['myfollowers'] = myfollowers
            context['myfollowing'] = myfollowing

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


class UserGroups(View):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        userdetails = UserProfile.objects.get(user=user)

        topics = Topic.objects.all()
        groups = user.group_set.all()
        group_posts = user.post_set.all()

        followers = userdetails.followers.all()
        following = userdetails.following.all()
        owned_groups = userdetails.owned_groups.all()
        followed_groups = userdetails.followed_groups.all()
        all_groups = followed_groups

        q = request.GET.get('q') if request.GET.get('q') is not None else ''

        if q == 'owned-groups':
            groups = userdetails.owned_groups.annotate(num_posts=Count('post')).order_by('-num_posts')
        else:
            groups = userdetails.followed_groups.annotate(num_posts=Count('post')).order_by('-num_posts')

        if not q:
            groups = userdetails.followed_groups.annotate(num_posts=Count('post')).order_by('-num_posts')


        

        context = {'user': user, 'topics': topics, 'groups': groups, 'group_posts' : group_posts, 'followers': followers, 'following': following, 'owned_groups': owned_groups, 'groups': groups, 'all_groups': all_groups}
        return render(request, 'base/profile-pages/owned-groups.html', context)


class Followers(View):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        userdetails = UserProfile.objects.get(user=user)
        if request.user.is_authenticated:
            mydetails = UserProfile.objects.get(user=request.user)
            myfollowers = mydetails.followers.all()
            myfollowing = mydetails.following.all()

        topics = Topic.objects.all()
        groups = user.group_set.all()
        group_posts = user.post_set.all()

        followers = userdetails.followers.all()
        following = userdetails.following.all()
        owned_groups = userdetails.owned_groups.all()
        followed_groups = userdetails.followed_groups.all()
        all_groups = followed_groups


        context = {'user': user, 'topics': topics, 'groups': groups, 'group_posts' : group_posts, 'followers': followers, 'following': following, 'owned_groups': owned_groups, 'all_groups': all_groups}
        return render(request, 'base/profile-pages/followers.html', context)


class Following(View):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        userdetails = UserProfile.objects.get(user=user)
        topics = Topic.objects.all()
        groups = user.group_set.all()
        group_posts = user.post_set.all()
        followers = userdetails.followers.all()
        following = userdetails.following.all()
        owned_groups = userdetails.owned_groups.all()
        followed_groups = userdetails.followed_groups.all()
        all_groups = followed_groups

        context = {'user': user, 'topics': topics, 'groups': groups, 'group_posts' : group_posts, 'followers': followers, 'following': following, 'owned_groups': owned_groups, 'all_groups': all_groups}
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
            if request.FILES.get('image') is None:
                group.image = 'group-image.png'
            else:
                group.image = request.FILES.get('image')
            group.save()
            group.participants.add(request.user)
            current_user = UserProfile.objects.get(user=request.user)
            current_user.owned_groups.add(group)
            
            return redirect('group', pk=group.id)

        topics = Topic.objects.all()
        context = {'form': form, 'topics': topics}
        return render(request, 'base/create_group_form.html', context)


@login_required(login_url='login')
def updateGroup(request, group_id):
  group = Group.objects.get(pk=group_id)
  form = GroupForm(request.POST or None, request.FILES or None, instance=group)

  old_image = group.image

  if request.user != group.host:
    return HttpResponse('You are not allowed to update')

  if request.method == 'POST':
    if form.is_valid():
        group = form.save(commit=False)
        group.image = request.FILES.get('image')
        if 'clear_image' in request.POST:
            if os.path.isfile(old_image.path) and old_image!="group-image.png":
                os.remove(old_image.path)
            group.image = 'group-image.png' 
        elif group.image == "" or group.image == None:
            group.image = old_image
        group.save()  

    return redirect('group', group.id)

  return render(request, 'base/update_group_form.html', {'group': group, 'form': form})


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


@login_required(login_url='login')
def deletePost(request, pk):
    print("1")
    post = Post.objects.get(id=pk)
    if request.user != post.user:
        print("2")
        return JsonResponse({'error': 'You are not allowed to delete'})
       
    if request.method == "POST":
        post.delete()
        print("3")
        return JsonResponse({'success': 'Post deleted successfully'})

    print("4")
    print(request.method)
    return JsonResponse({'error': 'Invalid request method'})


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


class ChatUserView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, pk):
        sender = User.objects.get(pk=request.user.id)
        receiver = User.objects.get(pk=pk)
        messages = ChatMessage.objects.filter(
            user=request.user, receiver=receiver
        ) | ChatMessage.objects.filter(
            user=receiver, receiver=request.user
        ).order_by('created')[:]

        form = ChatMessageForm()
        context = {
        'receiver': receiver,
        'messages': messages,
        'form': form,
        }
        #To avoid empty messages and bad words
        bad_words_list = ['cunt','cumbubble', 'fuck', 'f*ck', 'shit', 'piss', 'asshole', 'dickweed']
        end_chars = [' ', '.', ',', '!', ':', ';']
        mgs = ChatMessage.objects.all()
        for m in mgs:
            if m.message == "" and m.image=="":
                m.delete()
            m.message = m.message.lower()
            word = ""
            for char in m.message:
                if char in end_chars:
                    if word in bad_words_list:
                        m.delete()
                    word = ""
                else:
                    word+=char
            if word in bad_words_list:
                m.delete()
                
        return render(request, 'base/chat.html', context)

    def post(self, request, pk):
        form = ChatMessageForm(request.POST, request.FILES)
        sender = User.objects.get(pk=request.user.id)
        receiver = User.objects.get(pk=pk)
        if form.is_valid():
            message = form.save(commit=False)
            message.user = request.user
            message.receiver = receiver
            sender.profile.chatters.add(receiver)
            receiver.profile.chatters.add(sender)
            message.save()
            return JsonResponse({'success': 'Message sent successfully'})


def getNewMessage(request, pk):
    new_message_time = request.GET.get('new_message_time')
    receiver = User.objects.get(pk=pk)

    if new_message_time:
        new_message_time = datetime.fromtimestamp(float(new_message_time), timezone.utc)
        messages = ChatMessage.objects.filter(
            Q(user=request.user, receiver=receiver) | Q(user=receiver, receiver=request.user),
            created__gt=new_message_time
        ).order_by('-created')[:1]
    else:
        messages = ChatMessage.objects.filter(
            Q(user=request.user, receiver=receiver) | Q(user=receiver, receiver=request.user)
        ).order_by('-created')[:1]

    data = {
        'messages': [{'id': message.id, 'text': message.message, 'created': message.created.timestamp()} for message in messages]
    }

    return JsonResponse(data)


class ChatPageView(View):
    def get(self, request):
        user = User.objects.get(pk=request.user.id)
        chatters = user.profile.chatters.all()
        print(chatters)
        context = {'chatters': chatters}
        return render(request, 'base/chat_page.html', context)

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



"""
     # I used this to add old groups to owned_groups

    selected_groups = Group.objects.all()
    selected_users = UserProfile.objects.all()
    for user in selected_users:
        for group in selected_groups:
            if (str(user) == str(group.host)):
                user.owned_groups.add(group)


    Used this to give default profile photos to old users

    users = UserProfile.objects.all()
    for user in users:
        if user.profile_pic == "":
            user.profile_pic = 'noprofile.webp'
            user.save()
    

    Used this to give default group photos to old groups

    groups0 = Group.objects.filter(image__isnull=True)
    for group in groups0:
        group.image = 'group-image.png'
        group.save()


    
    Used this to add users their followed groups by collecting each participants of groups:

    us = UserProfile.objects.all()
    gs = Group.objects.all()

    for g in gs:
        for par in g.participants.all():
            par.profile.followed_groups.add(g)


    """

"""
@login_required(login_url='login')
@transaction.atomic
def updateUser(request):
    profile = UserProfile.objects.get(user=request.user.id)

    if profile.profile_pic != "noprofile.webp":
        old_profile_pic = profile.profile_pic
    else:
        old_profile_pic = None

    if request.method == 'POST':
        form = UserForm(request.POST, instance = request.user)
        form2 = UserForm2(request.POST, request.FILES, instance = request.user.profile)

        if form.is_valid() and form2.is_valid():

            # Check if the uploaded profile_pic size exceeds the limit
            if request.FILES.get('profile_pic') and request.FILES['profile_pic'].size > 10 * 1024 * 1024:
                return JsonResponse({'error': 'Image too big'})
            
            notform2 = form2.save(commit=False)

            cropped_image = request.POST.get('cropped_image')
            if cropped_image and ',' in cropped_image:
                profile_pic = ContentFile(base64.b64decode(cropped_image.split(',')[1]), name='profile_pic.jpg')
                notform2.profile_pic.save('profile_pic.jpg', profile_pic, save=False)

                
                if old_profile_pic:
                    if profile.profile_pic != "noprofile.webp":
                        old_profile_pic.delete(save=False)
                    notform2.save() # Save the change to the database
                    
                    
            elif not cropped_image and old_profile_pic:   
                if profile.profile_pic != "noprofile.webp":
                    old_profile_pic.delete(save=False)
                notform2.profile_pic = 'noprofile.webp'

            form.save()
            notform2.save()

            return redirect('user-profile', pk=request.user.id)
    else:
        form = UserForm(instance = request.user)
        form2 = UserForm2(instance = request.user.profile)

    context = {'form': form, 'form2': form2, 'profile': profile}
    return render(request, 'base/update_user.html', context)


    Used this to add people in group participants to followed groups:

    selected_groups = Group.objects.all()
    selected_users = User.objects.all()
    for user in selected_users:
        for group in selected_groups:
            if (user in group.participants.all()):
                user.profile.followed_groups.add(group)
"""