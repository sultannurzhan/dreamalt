from posixpath import pathsep
from . import views
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import handler500
from django.contrib.auth.decorators import login_required
from .views import like

urlpatterns = [
    path ('login/', views.LoginUser.as_view(), name="login"),
    path ('logout/', views.logoutUser, name="logout"),
    path ('register/', views.RegisterUser.as_view(), name="register"),

    path('', views.Home.as_view(), name="home"),

    path('group/<str:pk>/', views.GroupDetails.as_view(), name="group"), 
    path('group/<int:pk>/comments/<int:post_id>/', views.groupComments, name='group_comments'),
    path('group/<int:pk>/post/<int:post_id>/add_comment/', views.addComment, name='add_comment'),
    path('delete-comment/<int:commentId>/', views.deleteComment, name='delete-comment'),

    path('user<str:pk>/', views.UserProfileView.as_view(), name="user-profile"),

    path('create-group/', views.CreateGroupView.as_view(), name="create-group"),
    path('update-group/<str:group_id>/', views.updateGroup, name="update-group"),


    path('delete-group/<str:pk>/', views.deleteGroup, name="delete-group"),
    path('delete-post/<str:pk>/', views.deletePost, name="delete-post"), 

    path('update-user/', views.UpdateUserView.as_view(), name="update-user"), 
    path('group-page/', views.GroupPage.as_view(), name="group-page"), 

    path('user-groups/<str:pk>', views.UserGroups.as_view(), name="owned-groups"),
    path('followers/<str:pk>', views.Followers.as_view(), name="followers"),
    path('following/<str:pk>', views.Following.as_view(), name="following"),

    path('get-posts/', views.getPosts, name='get-posts'),
    path('like-post/<int:post_id>/', login_required(like), name='like-post'),
    path('login_required/', views.login_required_ajax_view, name='login_required'),

    path('follow/<int:pk>/', views.FollowGroup.as_view(), name='follow_group'),
    path('unfollow/<int:pk>/', views.UnfollowGroup.as_view(), name='unfollow_group'),

    path('chat/<int:pk>/', views.ChatUserView.as_view(), name='chat-user'),
    path('getNewMessage/<str:pk>/', views.getNewMessage, name='get-new-message'),
    path('chat-page/', views.ChatPageView.as_view(), name="chat-page"), 

    path ('about/', views.AboutView.as_view(), name="about"),
    path ('careers/', views.careers, name="careers"),
    path ('terms/', views.terms, name="terms"),
    path ('privacy/', views.privacy, name="privacy"),
    path ('business/', views.business, name="business"),
    path ('contact/', views.contact, name="contact"),
    path ('your-ad-choices/', views.yourAdChoices, name="your-ad-choices"),

    path('following-news/', views.FollowingNewsView.as_view(), name="following-news")
]

handler404 = 'base.views.handler404'

handler500 = handler500  # define the 500 error handler

# add the handler500 view to urlpatterns
urlpatterns += [path('500/', handler500, name='handler500')]