import copy, json, datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q, Max
from django.utils.crypto import get_random_string
from django.utils import timezone

from ratelimit.decorators import ratelimit

from .tasks import run, RepeatedTimer

import threading

from .models import Profile, Token, Group, Group_Member, WebhookTransaction, Snitch, Snitch_Record
from .forms import UserForm, ProfileForm, GroupForm, AddMember, PlayerFilter

# Create your views here.

def Home(request):
    context = {}
    if request.user.is_authenticated:
        ownerGroups = Group.objects.filter(owner=request.user)
        memberGroupIds = Group_Member.objects.filter(user=request.user).values('belongs')
        memberGroups = Group.objects.filter(id__in=memberGroupIds)
        tokens = Token.objects.filter(Q(group__in=ownerGroups) | Q(group__in=memberGroups))
        snitches = Snitch.objects.filter(token__in=tokens)
        date = datetime.datetime.now(tz=timezone.get_current_timezone()) - datetime.timedelta(minutes=15)
        alerts = Snitch_Record.objects.filter(snitch__in=snitches, pub_date__gte=date).order_by('-pub_date')
        array = []
        while (len(alerts) != 0):
            alert = alerts.first()
            array.append(alert)
            alerts = alerts.exclude(user=alert.user)
        context = {
                'list' : array
            }
    return render(request, 'home/home.html', context)

@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        #profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid():# and profile_form.is_valid():
            user_form.save()
            #profile_form.save()
            return HttpResponseRedirect('/')
        else:
            messages.error(request, ('Please correct the error below.'))
    else:
        user_form = UserForm(instance=request.user)
        #profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'home/profile.html', {
        'user_form': user_form
        #'profile_form': profile_form
    })
   
# This method handles displaying all your groups
@login_required
@transaction.atomic
def handle_group(request):
    error = None
    if request.method == 'POST':
        # This is for if user creates a group
        form = GroupForm(request.POST)
        if (form.is_valid()):
            n = form.cleaned_data['group_name']
            # Now need to check if the user already owns this group
            if len(Group.objects.filter(owner=request.user, name=n)) > 0:
                # Name exists
                error = {'error': 'Group already exists.'}
            else:
                # Name doesn't exist, time to create it
                group = Group(owner=request.user, name=n)
                group.save()
                return HttpResponseRedirect('/groups', error)
        else:
            error = {'error': 'Form is invalid'}
    # No group specified
    # Let's render the groups
    groups = Group.objects.filter(owner=request.user)
    sharedGroups = Group_Member.objects.filter(user=request.user)
    content = {
            'groupList' : groups,
            'sharedList' : sharedGroups
        }
    if not (error is None):
        content.update(error)
    return render(request, 'home/group.html', content)
           
@login_required
@transaction.atomic
def show_group(request, name, user=None):
    # We are rendering a specific group
    # First check if the group is being accessed by owner
    edit = False
    owner = False
    if user is None:
        group = get_object_or_404(Group, owner=request.user, name=name)
        edit = True
        owner = True
    else:
        # The user is being checked by a member or admin
        ownerObject = User.objects.get(username=user) # Owner of the group
        group = get_object_or_404(Group, owner=ownerObject, name=name)
        groupMember = get_object_or_404(Group_Member, belongs=group, user=request.user)
        if groupMember.permission == groupMember.ADMIN: # User is admin so had permission
            edit = True
    if request.method == 'POST' and edit:
        # The user added a member
        form = AddMember(request.POST)
        if form.is_valid():
            newMember = form.cleaned_data['name']
            perm = form.cleaned_data['permission']
            member = Group_Member(belongs=group, user=newMember[0], permission=Group_Member.PERMISSIONS[int(perm)][1])
            member.save()
    users = []
    try:
        # Get a list of members and render them
        group_members = Group_Member.objects.filter(belongs=group)
        for member in group_members:
            users.append({'username' : member.user.username, 'perm' : member.permission})
    except ObjectDoesNotExist:
        pass
        
    # Let's see if we should show the token.
    token = False
    if owner:
        # Is there a token.
        try:
            token = Token.objects.get(group=group)
            owner = False
        except ObjectDoesNotExist:
            pass
    content = {
        'group' : group,
        'userList' : users,
        'generateButton' : owner,
        'token' : token
    }
    if edit:
        try:
            add_member_form = AddMember(group=group, user=request.user)
            update = {'addMemberForm' : add_member_form}
            content.update(update)
        except ObjectDoesNotExist:
            pass
    return render(request, 'home/groups.html', content)
    
@login_required
@require_POST
@transaction.atomic
def remove_member(request, group, user, owner=None):
    # First let's check if the user has permission
    # Let's see if the user is the owner
    try:
        groupObject = Group.objects.get(name=group, owner=request.user)
        edit = True
    except ObjectDoesNotExist:
        edit = False
    if not edit:
        # User wasn't owner, let's see if they have admin
        if owner is None:
            # Quick easy check
            return HttpResponse(status=404)
        try:
            ownerObject = User.objects.get(username=owner)
            groupObject = Group.objects.get(name=group, owner=ownerObject)
            groupMember = Group_Member.objects.get(belongs=groupObject, user=request.user)
            if groupMember.permission != groupMember.ADMIN:
                return HttpResponse(status=404)
        except ObjectDoesNotExist:
            return HttpResponse(status=404)
    # If we are here then the user can edit
    deleteUser = User.objects.get(username=user)
    Group_Member.objects.get(belongs=groupObject, user=deleteUser).delete()
    if not owner is None:
        # Admin removed someone
        return HttpResponseRedirect('/groups/m/%s/%s' % (owner, group))
    else:
        # Owner
        return HttpResponseRedirect('/groups/o/%s' % group)
        
rt = None
@ratelimit(key='post:key', rate='60/m', block=True)
@csrf_exempt
@require_POST
def webhook(request, key):
    # Start the process
    global rt # TODO Make this not have to work this way
    if rt is None:
        rt = RepeatedTimer(10, run)
    try:
        token = Token.objects.get(api_key=key)
    except ObjectDoesNotExist:
        return HttpResponse(status=403)
    
    jsondata = request.body
    data = json.loads(jsondata.decode('utf8'))
    meta = copy.copy(request.META)
    #for k, v in meta.items():
    #    if not isinstance(v, basestring):
    #        del meta[k]
    
    WebhookTransaction.objects.create(
        date_generated=datetime.datetime.fromtimestamp(
            data['timestamp'], 
            tz=timezone.get_current_timezone()
        ),
        body=data,
        request_meta=meta,
        token = token
    )
    return HttpResponse(status=200)
  
@login_required
@require_POST
@transaction.atomic
def generate_token(request, group):
    # First need to make sure request is valid
    try:
        groupObject = Group.objects.get(name=group, owner=request.user)
    except ObjectDoesNotExist:
        return HttpResponse(status=403)
    # Now generate a token
    Token.objects.create(group=groupObject, api_key=get_random_string(length=32))
    return HttpResponseRedirect('/groups/o/%s' % group)
    
@login_required
@transaction.atomic
def view_snitches(request):
    # So I only want owners of a group to be able to modify which groups their snitches can report to.
    # Also if they are admin of a group they can add snitches to that group.
    # Lets get all their snitches they are owner of.
    groups = Group.objects.filter(owner=request.user)
    tokens = Token.objects.filter(group__in=groups)
    snitchGroups = Snitch.objects.filter(token__in=tokens)
    # Now to do the list of groups the user is admin of.
    groupAdminsIds = Group_Member.objects.filter(user=request.user, permission=Group_Member.PERMISSIONS[Group_Member.ADMIN][1]).values('belongs')
    groupAdmins = Group.objects.filter(id__in=groupAdminsIds)
    tokenAdmins = Token.objects.filter(group__in=groupAdmins)
    snitchAdmins = Snitch.objects.filter(token__in=tokenAdmins)
    
    content = {
        'ownerGroups' : snitchGroups,
        'adminGroups' : snitchAdmins
    }
    return render(request, 'snitches/snitches.html', content)
    
@login_required
@transaction.atomic
def view_alerts(request):
    # This method is used to display all the snitch events.
    player_name = None
    start_time = None
    end_time = None
    player_filter = PlayerFilter()
    if request.method == 'POST':
        # Let's look at search results that have come
        player_filter = PlayerFilter(request.POST)
        if player_filter.is_valid():
            player_name = player_filter.cleaned_data['search_bar']
            start_time = player_filter.cleaned_data['start_date_field']
            endTime = player_filter.cleaned_data['end_date_field']
    # Let's get all the snitch records this user has access to.
    ownerGroups = Group.objects.filter(owner=request.user)
    memberGroupIds = Group_Member.objects.filter(user=request.user).values('belongs')
    memberGroups = Group.objects.filter(id__in=memberGroupIds)
    tokens = Token.objects.filter(Q(group__in=ownerGroups) | Q(group__in=memberGroups))
    snitches = Snitch.objects.filter(token__in=tokens)
    alerts = Snitch_Record.objects.filter(snitch__in=snitches).order_by('-pub_date')
    if start_time:
        alerts = alerts.filter(pub_date__gte=start_time)
    if end_time:
        alerts = alerts.filter(pub_date__lte=end_time)
    if player_name:
        alerts = alerts.filter(user=player_name)
    
    content = {
        'alerts' : alerts,
        'playerFilterForm' : player_filter
    }
    return render(request, 'snitches/alerts.html', content)
    
def logout_view(request):
    logout(request)
    return render(request, 'home/home.html')