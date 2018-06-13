from django.shortcuts import redirect, HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.models import User
from snitches.models import Profile, Group_Member
from django import forms

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)
        
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('token',)
        
class GroupForm(forms.Form):
    group_name = forms.CharField(label='Group name', max_length=20)
    
class AddMember(forms.ModelForm):
    class Meta:
        model = Group_Member
        fields = ('user', 'permission',)