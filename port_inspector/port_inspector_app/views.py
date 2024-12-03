from django.shortcuts import render
from django.template import loader
from django.conf import settings
from . import forms
from .models import ImageSet

# Create your views here.
def upload_image(request):
    # if the user is attempting to POST, aka submitting the form
    if request.method == "POST":
        #form filled with the request information
        image_form = forms.ImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            new_image_set = image_form.save(commit=False)
            new_image_set.save()
            #potentially redirect to a new page here
    #else it is a GET request, meaning the user is requesting the page, in which we should give them an empty form
    else:
        image_form = forms.ImageForm()  
    return render(request, 'upload_photo.html', {'form' : image_form})


def view_history(request):
    image_sets = ImageSet.objects.all()
    return render(request, 'history.html', {'images' : image_sets, 'MEDIA_URL' : settings.MEDIA_URL})