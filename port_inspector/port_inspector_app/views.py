from django.shortcuts import render, redirect
from django.template import loader
from django.conf import settings
from . import forms
from port_inspector_app.models import Image, SpecimenUpload
from .forms import UserRegisterForm
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib import messages

User = get_user_model()


def verify_email(request):
    if request.method == "POST":
        if not request.user.is_email_verified:
            current_site = get_current_site(request)
            user = request.user
            email = request.user.email
            subject = "Verify Email"
            message = render_to_string('verify-email-message.html', {
                'request': request,
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            email = EmailMessage(
                subject, message, to=[email]
            )
            email.content_subtype = 'html'
            email.send()
            return redirect('verify-email-done')
        else:
            return redirect('signup')
    return render(request, 'verify-email.html')


def verify_email_done(request):
    return render(request, 'verify-email-done.html')


def verify_email_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):  # noqa: E275
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_email_verified = True
        user.save()
        messages.success(request, 'Your email has been verified.')
        return redirect('verify-email-complete')
    else:
        messages.warning(request, 'The link is invalid.')
    return render(request, 'verify-email-confirm.html')


def verify_email_complete(request):
    return render(request, 'verify-email-complete.html')


def signup_view(request):
    if request.method == "POST":
        print("signup POST request recieved\n")
        next = request.GET.get('next')
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            new_user = authenticate(email=user.email, password=password)
            if new_user:
                login(request, new_user)
                return redirect('verify-email')
            else:
                print("Authentication failed")
            if next:
                return redirect(next)
            else:
                return redirect('verify-email')
        else:
            print("ERROR: Email already in use or passwords do not match\n")
    else:
        form = UserRegisterForm()
    context = {
        'form': form
    }
    return render(request, 'signup.html', context)


def login_view(request):
    # if receiving a POST method, user is attempting to login
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        # if user is properly authenticated
        if form.is_valid():
            login(request, form.get_user())
            return redirect("/upload/")  # after the user logs in, send them to the homepage
    # if user is already logged in, redirect
    elif request.user.is_authenticated:
        return redirect('/upload/')
    # if requesting the page, prompt form for authentication
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


# log the user out and send them back to the upload page
def logout_view(request):
    logout(request)
    return redirect("/upload/")


# Create your views here.
def upload_image(request):
    # if the user is attempting to POST, aka submitting the form
    if request.method == "POST":
        # form filled with the request information
        image_form = forms.ImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            # generate a new specimen upload
            specimen_upload = SpecimenUpload()
            # TODO implement user session
            specimen_upload.user = None  # placeholder, set user to null for now

            new_image = image_form.save(commit=False)
            new_image.specimen_upload = specimen_upload

            specimen_upload.save()
            new_image.save()
            # potentially redirect to a new page here
    # else it is a GET request, meaning the user is requesting the page, in which we should give them an empty form
    else:
        image_form = forms.ImageForm()
    return render(request, 'upload_photo.html', {'form': image_form})


def view_history(request):
    image_sets = Image.objects.all()
    return render(request, 'history.html', {'images': image_sets, 'MEDIA_URL': settings.MEDIA_URL})
