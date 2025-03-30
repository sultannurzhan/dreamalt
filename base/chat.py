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
        received_messages = ChatMessage.objects.filter(receiver=user)
        sent_messages = ChatMessage.objects.filter(user=user)
        last_received_messages = []

        hasSameUser = False
        for message in received_messages:
            for last_message in last_received_messages:
                if message.user == last_message.user:
                    hasSameUser = True
                    if message.created > last_message.created:              
                        last_received_messages.remove(last_message)
                        last_received_messages.append(message)
            if hasSameUser == False:
                last_received_messages.append(message)

        last_sent_messages = []
        hasSameUser = False
        for message in sent_messages:
            for last_message in last_sent_messages:
                if message.receiver == last_message.receiver:
                    hasSameUser = True
                    if message.created > last_message.created:
                        last_sent_messages.remove(last_message)
                        last_sent_messages.append(message)
            if hasSameUser == False:
                last_sent_messages.append(message)

  
        context = {'chatters': chatters, 'received_messages': received_messages, 'last_received_messages': last_received_messages, 'last_sent_messages': last_sent_messages}
        return render(request, 'base/chat_page.html', context)
