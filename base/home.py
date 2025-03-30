from django.views import View
from .models import *
from .forms import *
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.db.models.functions import Random
from django.shortcuts import get_object_or_404, render, redirect

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

