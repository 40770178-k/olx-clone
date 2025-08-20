from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Item

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class ItemForm(forms.ModelForm):

    location = forms.CharField(max_length=100, required=False, help_text='Optional. Specify the location of the item.')
    class Meta:
        model = Item       # link form to Item model
        fields = ['title', 'description', 'price', 'category', 'location', 'image']

        def clean_location(self):
            data = self.cleaned_data['location']
            if not data:
                return "Unknown"
            return data