from posixpath import pathsep
from . import views, auth, home, group, post, comment, user, chat
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import handler500
from django.contrib.auth.decorators import login_required

urlpatterns = [
    #Functional Pages
    path('', home.Home.as_view(), name="home"),
    path('group-page/', views.GroupPage.as_view(), name="group-page"), 
    path('following-news/', views.FollowingNewsView.as_view(), name="following-news"),

    #Auth
    path('login/', auth.LoginUser.as_view(), name="login"),
    path('logout/', auth.logoutUser, name="logout"),
    path('register/', auth.RegisterUser.as_view(), name="register"),
    path('login_required/', views.login_required_ajax_view, name='login_required'),

    #Group
    path('group/<str:pk>/', group.GroupDetails.as_view(), name="group"), 
    path('create-group/', group.CreateGroupView.as_view(), name="create-group"),
    path('suggest-topics/', group.suggest_topics, name='suggest-topics'),
    path('update-group/<str:group_id>/', group.UpdateGroupView.as_view(), name="update-group"),
    path('delete-group/<str:pk>/', group.deleteGroup, name="delete-group"),
    path('follow/<int:pk>/', group.FollowGroup.as_view(), name='follow_group'),
    path('unfollow/<int:pk>/', group.UnfollowGroup.as_view(), name='unfollow_group'),

    #Post
    path('group/<int:pk>/add-post/', post.AddPostView.as_view(), name='add-post'),
    path('get-posts/', post.getPosts, name='get-posts'),
    path('like-post/<int:post_id>/', login_required(post.like_post), name='like-post'),
    path('delete-post/<str:pk>/', post.deletePost, name="delete-post"), 

    #Comment
    path('group/<int:pk>/comments/<int:post_id>/', comment.groupComments, name='group_comments'),
    path('group/<int:pk>/post/<int:post_id>/add_comment/', comment.addComment, name='add_comment'),
    path('delete-comment/<int:commentId>/', comment.deleteComment, name='delete-comment'),

    #User
    path('user<str:pk>/', user.UserProfileView.as_view(), name="user-profile"),
    path('user-groups/<str:pk>', user.UserGroups.as_view(), name="owned-groups"),
    path('followers/<str:pk>', user.Followers.as_view(), name="followers"),
    path('following/<str:pk>', user.Following.as_view(), name="following"),
    path('update-user/', user.UpdateUserView.as_view(), name="update-user"), 
    
    #Chat
    path('chat/<int:pk>/', chat.ChatUserView.as_view(), name='chat-user'),
    path('getNewMessage/<str:pk>/', chat.getNewMessage, name='get-new-message'),
    path('chat-page/', chat.ChatPageView.as_view(), name="chat-page"), 

    #Static Pages
    path ('about/', views.AboutView.as_view(), name="about"),
    path ('careers/', views.careers, name="careers"),
    path ('terms/', views.terms, name="terms"),
    path ('privacy/', views.privacy, name="privacy"),
    path ('business/', views.business, name="business"),
    path ('contact/', views.contact, name="contact"),
    path ('your-ad-choices/', views.yourAdChoices, name="your-ad-choices"),
]

handler404 = 'base.views.handler404'

handler500 = handler500  # define the 500 error handler

# add the handler500 view to urlpatterns
urlpatterns += [path('500/', handler500, name='handler500')]