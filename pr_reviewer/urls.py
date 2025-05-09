from django.contrib import admin
from django.urls import path
from pr_reviewer.views.bitbucket_view import get_config, index, get_repository
from pr_reviewer.views.view import api_view_pull_request, config_workspace

urlpatterns = [
    path('home/', index),
    path('api/config/', get_config), #no need
    path('api/<str:workspace>/', get_repository),

    # POST
    path('api/filter', api_view_pull_request, name='filter'),
    path('api/workspace/config', config_workspace, name='filter'), #no need
]
