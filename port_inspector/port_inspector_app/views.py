from django.shortcuts import render
from django.template import loader
from django.conf import settings
from . import forms
from port_inspector_app.models import Image, SpecimenUpload

# Create your views here.
def upload_image(request):
    # if the user is attempting to POST, aka submitting the form
    if request.method == "POST":
        #form filled with the request information
        image_form = forms.ImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            #generate a new specimen upload
            specimen_upload = SpecimenUpload()
            #TODO implement user session
            specimen_upload.user = None #placeholder, set user to null for now

            new_image = image_form.save(commit=False)
            new_image.specimen_upload = specimen_upload

            specimen_upload.save()
            new_image.save()
            #potentially redirect to a new page here
    #else it is a GET request, meaning the user is requesting the page, in which we should give them an empty form
    else:
        image_form = forms.ImageForm()  
    return render(request, 'upload_photo.html', {'form' : image_form})


def view_history(request):
    image_sets = Image.objects.all()
    return render(request, 'history.html', {'images' : image_sets, 'MEDIA_URL' : settings.MEDIA_URL})