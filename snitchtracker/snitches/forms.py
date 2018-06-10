from django.shortcuts import redirect, HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.models import User
from snitches.models import Profile
from django import forms

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)
        
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('token',)