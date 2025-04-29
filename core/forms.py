from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import os

from .models import Post, Profile

# ---------- yardımcı doğrulayıcılar ----------
def validate_file_size(f):
    if f.size > 5 * 1024 * 1024:        # 5 MB
        raise ValidationError("File is larger than 5 MB.")

def validate_extension(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in {'.pdf', '.png', '.jpg', '.jpeg', '.txt'}:
        raise ValidationError("Only PDF, PNG, JPG, JPEG, TXT files allowed.")
# ------------------------------------------------

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class PostForm(forms.ModelForm):
    file = forms.FileField(required=False,
                           validators=[validate_file_size, validate_extension])
    class Meta:
        model = Post
        fields = ['title', 'content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={'rows':5,
                                             'placeholder':'Write your content here…'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows':4,
                                         'placeholder':'Tell us about yourself…'}),
        }
