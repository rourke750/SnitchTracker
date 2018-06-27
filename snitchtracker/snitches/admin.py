"""Admin class

    This class handles which dbs the admin can see.
"""
from django.contrib import admin
from django.contrib.admin.models import LogEntry

from .models import Group, GroupMember, Snitch, \
    SnitchRecord, SnitchGroup, Token, WebhookTransaction

# Register your models here.
admin.site.register(Group)
admin.site.register(GroupMember)
admin.site.register(Snitch)
admin.site.register(SnitchRecord)
admin.site.register(SnitchGroup)
admin.site.register(WebhookTransaction)
admin.site.register(Token)
admin.site.register(LogEntry)
