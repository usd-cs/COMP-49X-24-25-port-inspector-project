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
    frontal_upload = forms.ImageField(required=False)
    dorsal_upload = forms.ImageField(required=False)
    caudal_upload = forms.ImageField(required=False)
    lateral_upload = forms.ImageField(required=False)

    class Meta:
        model = models.SpecimenUpload
        fields = []

    def clean(self):
        cleaned_data = super().clean()

        # Check if at least one image field has a file uploaded.
        if not any([
            cleaned_data.get("frontal_upload"),
            cleaned_data.get("dorsal_upload"),
            cleaned_data.get("caudal_upload"),
            cleaned_data.get("lateral_upload")
        ]):
            raise forms.ValidationError("You must upload at least one image.")
        return cleaned_data

    # Override save function so that we save the image data as 'Image' objects in our table
    # first, then reference those objects to our SpecimenUpload
    def save(self, commit=True, user=None):
        specimen = super().save(commit=False)

        if user:
            specimen.user = user

        if commit:
            specimen.save()  # Must save the SpecimenUpload first

            def generate_image_object(data):
                if data:
                    return models.Image.objects.create(specimen_upload=specimen, image=data)
                return None

            frontal_obj = generate_image_object(self.cleaned_data.get("frontal_upload"))
            dorsal_obj = generate_image_object(self.cleaned_data.get("dorsal_upload"))
            caudal_obj = generate_image_object(self.cleaned_data.get("caudal_upload"))
            lateral_obj = generate_image_object(self.cleaned_data.get("lateral_upload"))

            specimen.frontal_image = frontal_obj
            specimen.dorsal_image = dorsal_obj
            specimen.caudal_image = caudal_obj
            specimen.lateral_image = lateral_obj

            specimen.save()  # Save again for the FK fields

        return specimen

class ConfirmIdForm(forms.ModelForm):
    choice = forms.ChoiceField(label="Confirm Identification:", choices=[], widget=forms.Select())

    class Meta:
        model = models.SpecimenUpload
        fields = ['choice']

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])
        super().__init__(*args, **kwargs)
        self.fields['choice'].choices = choices