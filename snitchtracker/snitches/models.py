from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

import random

from jsonfield import JSONField

# Create your models here.

# This class represents which the snitches belong to.
# Each user is given a group by default.
class Group(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE) # The owner.
    name = models.CharField(max_length=32) # Name of the group.
    
# This class handles which webcall goes to which group
class Token(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE) # The group.
    api_key = models.CharField(max_length=32)
    
class Group_Member(models.Model):
    belongs = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ADMIN = 0
    MEMBER = 1
    PERMISSIONS = (
        (ADMIN, 'Admin'),
        (MEMBER, 'Member'),
    )
    permission = models.CharField(
        max_length=2,
        choices=PERMISSIONS,
        default=MEMBER,
    )
    
class Snitch(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE) # The token.
    name = models.CharField(max_length=40) # Name of the snitch.
    x_pos = models.IntegerField(default=0) # x pos of the snitch.
    y_pos = models.IntegerField(default=0) # y pos of the snitch.
    z_pos = models.IntegerField(default=0) # z pos of the snitch.
    world = models.CharField(max_length=100) # The world the snitch is in.
    server = models.CharField(max_length=100) # The server this snitch belongs to.

    # This class handles individual snitch messages.
class Snitch_Record(models.Model):
    snitch = models.ForeignKey(Snitch, on_delete=models.CASCADE) # The snitch.
    ENTERED = 'Et'
    LOGGED_IN = 'Li'
    LOGGED_OUT = 'Lo'
    TYPES = (
        (ENTERED, 'Entered'),
        (LOGGED_IN, 'Logged in'),
        (LOGGED_OUT, 'Logged out'),
    )
    type = models.CharField(
        max_length=2,
        choices=TYPES,
        default=None,
    )
    user = models.CharField(max_length=16) # The Minecraft username of the player who entered.
    pub_date = models.DateTimeField('date published', default=None)
    # Currently incomplete, once finalize what details we want will update
    
# This class represents a connector from a snitch record to the group.
class Snitch_Group(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    snitch = models.ForeignKey(Snitch, on_delete=models.CASCADE)
    
class Profile(models.Model):
    user = models.OneToOneField(User,unique=True, null=False, db_index=True, on_delete=models.CASCADE)
    token = models.TextField(max_length=36, blank=True)
    
class WebhookTransaction(models.Model):
    UNPROCESSED = 'UN'
    PROCESSED = 'PR'
    ERROR = 'ER'

    STATUSES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

    date_generated = models.DateTimeField()
    date_received = models.DateTimeField(default=timezone.now)
    body = JSONField()
    request_meta = models.TextField()
    status = models.CharField(max_length=250, choices=STATUSES, default=UNPROCESSED)
    token = models.ForeignKey(Token, on_delete=models.CASCADE) # The token.

    def __unicode__(self):
        return u'{0}'.format(self.date_event_generated)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        instance.username='newuser'+str(random.randint(1,9999999999999))
        Profile.objects.create(user=instance)
        # We also want to create a group for them
        Group.objects.create(owner=instance, name='Default Group')

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()