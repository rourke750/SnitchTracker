from django.contrib import admin

from .models import Group, Group_Member, Snitch, Snitch_Record, Snitch_Group, Token, WebhookTransaction
from django.contrib.admin.models import LogEntry
# Register your models here.
admin.site.register(Group)
admin.site.register(Group_Member)
admin.site.register(Snitch)
admin.site.register(Snitch_Record)
admin.site.register(Snitch_Group)
admin.site.register(WebhookTransaction)
admin.site.register(Token)
admin.site.register(LogEntry)