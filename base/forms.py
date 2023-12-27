from tkinter import Widget
from django.forms import ModelForm
from .models import Group, Post, UserProfile, ChatMessage
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    #first_name = forms.CharField(max_length=50,strip=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    #last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))

    username = forms.CharField(
        label = ("Username"),
        strip = False,
        widget = forms.TextInput(attrs={'class':'form-control'})
    )

    password1 = forms.CharField(
        label=("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class':'form-control'})
    )
    password2 = forms.CharField(
        label=("Password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class':'form-control'})

    )


    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2',)

    """
    def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
    """


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('topic', 'title', 'group_type', 'description')

        
        widgets = {
            'topic': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'group_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        

        

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        help_texts = {
            'username': None,
            'email': None
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserForm2(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'bio']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['body', 'image']
        labels = {
            "body": ""
        }


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ('message', 'image')
        labels = {
            "message": "",
        }
 