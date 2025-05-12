from django.contrib import admin
from django.urls import path
from pr_reviewer.views.bitbucket_view import index, get_repository
from pr_reviewer.views.view import api_view_pull_request

urlpatterns = [
    path('home/', index),
    path('api/<str:workspace>/', get_repository),

    # POST
    path('api/filter', api_view_pull_request, name='filter'),
]
