from django.contrib import admin

from .models import Group, Group_Member, Snitch_Details

# Register your models here.
admin.site.register(Group)
admin.site.register(Group_Member)
admin.site.register(Snitch_Details)