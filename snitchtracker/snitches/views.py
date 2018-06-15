import copy, json, datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils.crypto import get_random_string

from .models import Profile, Token, Group, Group_Member
from .forms import UserForm, ProfileForm, GroupForm, AddMember

# Create your views here.

def Home(request):
    return render(request, 'home/home.html')

@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return HttpResponseRedirect('/')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'home/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
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
        
@csrf_exempt
@require_POST
def webhook(request, key):
    try:
        token = Token.objects.get(api_key=key)
    except ObjectDoesNotExist:
        return HttpResponse(status=403)
    
    jsondata = request.body
    data = json.loads(jsondata)
    meta = copy.copy(request.META)
    for k, v in meta.items():
        if not isinstance(v, basestring):
            del meta[k]

    WebhookTransaction.objects.create(
        date_event_generated=datetime.datetime.fromtimestamp(
            data['timestamp']/1000.0, 
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
    
def logout_view(request):
    logout(request)
    return render(request, 'home/home.html')