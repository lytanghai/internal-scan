from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('pull_request/', include('pr_reviewer.urls')),
]
