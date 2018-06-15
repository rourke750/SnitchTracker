from django.conf.urls import url
from django.urls import path
from . import views

app_name='snitches'

urlpatterns = [
    #/$
    url(r'^profile', views.update_profile),
    path(r'groups', views.handle_group),
    path(r'groups/o/<str:name>', views.show_group), # For Owner
    path(r'groups/o/<str:group>/r/<str:user>', views.remove_member), # For owner
    path(r'groups/m/<str:name>/<str:user>', views.show_group), # For anyone but owner
    path(r'groups/m/<str:owner>/<str:group>/r/<str:user>', views.remove_member), # For anyone but owner
    url(r'^logout', views.logout_view),
    path(r'api/webhook/<str:key>', views.webhook),
    url(r'^', views.Home),
]