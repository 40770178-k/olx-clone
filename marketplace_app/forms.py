from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Item, ItemImage
from django import forms
from .models import Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class ItemForm(forms.ModelForm):
    # Multiple image upload field for extra images
    extra_images = forms.FileField(
        required=False,
        help_text='Upload additional images (optional). You can select multiple files.',
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )
    
    location = forms.CharField(max_length=100, required=False, help_text='Optional. Specify the location of the item.')
    
    class Meta:
        model = Item       # link form to Item model
        fields = ['title', 'description', 'price', 'category', 'location', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_location(self):
        data = self.cleaned_data['location']
        if not data:
            return "Unknown"
        return data


class ItemImageForm(forms.ModelForm):
    class Meta:
        model = ItemImage
        fields = ['image']
        


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }