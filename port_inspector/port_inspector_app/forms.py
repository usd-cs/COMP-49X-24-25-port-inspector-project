from django import forms
from . import models
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

User = get_user_model()


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(label='Password')

    class Meta:
        model = User
        fields = [
            'email',
            'password'
        ]

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        email_check = User.objects.filter(email=email)
        if email_check.exists():
            raise forms.ValidationError('This Email already exists')
        if len(password) < 5:
            raise forms.ValidationError('Your password should have more than 5 characters')
        return super(UserRegisterForm, self).clean(*args, **kwargs)


class ImageForm(forms.ModelForm):
    class Meta:
        model = models.Image
        fields = ['image']

class SpecimenUploadForm(forms.ModelForm):
    class Meta:
        model = models.SpecimenUpload
        fields = ['frontal_image', 'dorsal_image', 'caudal_image', 'lateral_image']

    # Make image fields optional in the form
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

ImageFormSet = inlineformset_factory(models.SpecimenUpload, models.Image, fields=['image'], extra=4, max_num=4, can_delete=True)

