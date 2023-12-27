from django.contrib import admin
from .models import ChatMessage, Group, Like, Topic, Post, Comment, UserProfile 
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

admin.site.register(Group)
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(UserProfile)
admin.site.register(ChatMessage)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class AccountsUserAdmin(AuthUserAdmin):
    def add_view(self, *args, **kwargs):
        self.inlines =[]
        return super(AccountsUserAdmin, self).add_view(*args, **kwargs)

    def change_view(self, *args, **kwargs):
        self.inlines =[UserProfileInline]
        return super(AccountsUserAdmin, self).change_view(*args, **kwargs)


admin.site.unregister(User)
admin.site.register(User, AccountsUserAdmin)