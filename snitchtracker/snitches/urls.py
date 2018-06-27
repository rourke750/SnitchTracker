"""Module used for listening to url patterns.
"""
from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'snitches'

urlpatterns = [
    #/$
    url(r'^profile', views.update_profile),
    path(r'groups', views.handle_group),
    path(r'groups/o/<str:name>', views.show_group), # For Owner
    path(r'groups/o/<str:group>/r/<str:user>', views.remove_member), # For owner
    path(r'groups/m/<str:user>/<str:name>', views.show_group), # For anyone but owner
    path(r'groups/m/<str:owner>/<str:group>/r/<str:user>', views.remove_member), # For anyone
    # but owner
    path(r'groups/o/<str:group>/t/generate', views.generate_token), # Generating a token
    path(r'snitches', views.view_snitches), # List all snitches
    path(r'alerts', views.view_alerts),
    url(r'^logout', views.logout_view),
    path(r'api/webhook/<str:key>', views.webhook),
    url(r'^', views.home),
]
