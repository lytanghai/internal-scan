from django.contrib import admin
from django.urls import path,include
from pr_reviewer.views.bitbucket_view import get_config, index, get_repository

urlpatterns = [
    path('pull_request/', include('pr_reviewer.urls')),
]
