from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Assign default profile picture to users who do not have one'

    def handle(self, *args, **kwargs):
        users = User.objects.filter(profile__profile_pic__isnull=True)
        for user in users:
            user.profile.profile_pic = 'profile-images/noprofile.webp'
            user.profile.save()