from django.conf.urls import url
from . import views

app_name='snitches'

urlpatterns = [
    #/$
    url(r'^profile', views.update_profile),
    url(r'^logout', views.logout_view),
    url(r'^', views.Home),
]