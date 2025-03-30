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
