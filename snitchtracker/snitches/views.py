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
    content = {'groupList' : groups}
    if not (error is None):
        content.update(error)
    return render(request, 'home/group.html', content)
        
@login_required
@transaction.atomic
def show_group(request, name):
    if request.method == 'POST':
        pass
    # We are rendering a specific group
    group = get_object_or_404(Group, owner=request.user, name=name)
    users = []
    try:
        group_members = Group_Member.objects.filter(belongs=group)
        for member in group_members:
            users.append({'username' : member.user.username, 'perm' : member.permission})
    except ObjectDoesNotExist:
        pass
    add_member_form = AddMember()
    content = {
        'group' : group,
        'userList' : users,
        'addMemberForm' : add_member_form
    }
    return render(request, 'home/groups.html', content)
        
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
        group = token.group
    )

    return HttpResponse(status=200)

def logout_view(request):
    logout(request)
    return render(request, 'home/home.html')