from django.shortcuts import redirect, HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.models import User
from snitches.models import Profile, Group_Member
from django import forms

from django.utils import timezone 

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username',)
        
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('token',)
        
class GroupForm(forms.Form):
    group_name = forms.CharField(label='Group name', max_length=32)
    
class AddMember(forms.Form):
    def __init__(self, *args,**kwargs):
        try:
            group = kwargs.pop('group')
            user = kwargs.pop('user')
            members = Group_Member.objects.filter(belongs=group)
            users = User.objects.all().exclude(id=user.id)
            for member in members:
                users = users.exclude(id=member.user.id)
            
            names = forms.ModelMultipleChoiceField(queryset=users)
            super(AddMember,self).__init__(*args,**kwargs)
            self.fields['name'] = names
        except KeyError:
            super(AddMember,self).__init__(*args,**kwargs)
    
    name = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    permission = forms.CharField(
            max_length=2,
            widget=forms.Select(choices=Group_Member.PERMISSIONS),
        )
        
class PlayerFilter(forms.Form):
    search_bar = forms.CharField(label='Search Bar', widget=forms.TextInput, max_length=16, required=False)
    start_date_field = forms.DateTimeField(label = 'Start', initial=timezone.now, required=False)
    end_date_field = forms.DateTimeField(label = 'End', initial=timezone.now, required=False)