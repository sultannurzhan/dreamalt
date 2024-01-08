from pydoc import describe
from tokenize import blank_re
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import MaxValueValidator


class Topic(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Group(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=False)      # <--- This is the relationship between two tables, which are Topic and Room
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(blank=True, upload_to="images/", default='group-image.png')

    PUBLIC = "public"
    PRIVATE = "private"
    GROUP_TYPE_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private')
    ]

    group_type = models.CharField(max_length=7, choices=GROUP_TYPE_CHOICES, default=PUBLIC)

    #Ordering the rooms. '-' is for newest first
    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.title



class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)         # <--- If a user deletes account??? all the messages will be deleted
    group = models.ForeignKey(Group, on_delete=models.CASCADE)         # <--- If a room is deleted all the message in the room will be deleted
    body = models.TextField(null=True, blank=True, max_length=3000)
    image = models.ImageField(null=True, blank=True, upload_to="post-images/")
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, through='Like', related_name='likes', blank=True)

    def is_liked(self, user):
        return self.likes.filter(id=user.id).exists()

    def __str__(self):
        return self.body[0:100]

    class Meta:
        ordering = ['-updated', '-created']

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_images")
    image = models.ImageField(upload_to='post-images/', blank=True, null=True)

    def __str__(self):
        return self.id + ": " + self.post.body


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    body = models.TextField(null=True, blank=False, max_length=1000)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.body[0:100]

    class Meta:
        ordering = ['-updated', '-created']


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)




class UserProfile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(200)])
    bio = models.TextField(null=True, blank=True)
    profile_pic = models.ImageField(blank=True, upload_to="profile-images/", default='noprofile.webp')
    followers = models.ManyToManyField(User, related_name='followers', blank=True)
    following = models.ManyToManyField(User, related_name="following", blank=True)
    owned_groups = models.ManyToManyField(Group, related_name="owned_groups", blank=True)
    followed_groups = models.ManyToManyField(Group, related_name="followed_groups", blank=True)
    chatters = models.ManyToManyField(User, related_name="chatters", blank=True)

    def __str__(self):
        return str(self.user)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receivers")
    message = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to="message-images/")
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return str(self.user)

