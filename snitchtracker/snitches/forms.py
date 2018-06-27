"""This module handles all forms related to the browser.
"""
from django.contrib.auth.models import User
from django.utils import timezone
from django import forms
from snitches.models import Profile, GroupMember

class UserForm(forms.ModelForm):
    """User form for users submitting username change.
    """

    class Meta:
        model = User
        fields = ('username',)

class ProfileForm(forms.ModelForm):
    """Profile form for users to update their profile, currently not used.
    """

    class Meta:
        model = Profile
        fields = ('token',)

class GroupForm(forms.Form):
    """Group form used for users to create a group.
    """

    group_name = forms.CharField(label='Group name', max_length=32)

class AddMember(forms.Form):
    """AddMember form for users to add members to groups.
    """

    def __init__(self, *args, **kwargs):
        try:
            group = kwargs.pop('group')
            user = kwargs.pop('user')
            members = GroupMember.objects.filter(belongs=group)
            users = User.objects.all().exclude(id=user.id)
            for member in members:
                users = users.exclude(id=member.user.id)

            names = forms.ModelMultipleChoiceField(queryset=users)
            super(AddMember, self).__init__(*args, **kwargs)
            self.fields['name'] = names
        except KeyError:
            super(AddMember, self).__init__(*args, **kwargs)

    name = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    permission = forms.CharField(
        max_length=2,
        widget=forms.Select(choices=GroupMember.PERMISSIONS),
    )

class PlayerFilter(forms.Form):
    """Player filter used for user to filter snitch alerts.
    """

    search_bar = forms.CharField(
        label='Search Bar',
        widget=forms.TextInput,
        max_length=16,
        required=False
    )
    start_date_field = forms.DateTimeField(label='Start', initial=timezone.now, required=False)
    end_date_field = forms.DateTimeField(label='End', initial=timezone.now, required=False)
