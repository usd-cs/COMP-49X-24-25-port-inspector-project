from django import forms
from . import models

class ImageForm(forms.ModelForm):
    class Meta:
        model = models.ImageSet
        fields = ['image']