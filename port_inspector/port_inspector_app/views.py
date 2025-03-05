from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from port_inspector_app.models import Image, SpecimenUpload, KnownSpecies, Genus

from . import forms
from .forms import UserRegisterForm
from .tokens import account_activation_token

User = get_user_model()


def verify_email(request):
    if request.method == "POST":
        if not request.user.is_email_verified:
            current_site = get_current_site(request)
            user = request.user
            email = request.user.email
            subject = "Verify Email"
            message = render_to_string(
                "verify-email-message.html",
                {
                    "request": request,
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": account_activation_token.make_token(user),
                },
            )
            email = EmailMessage(subject, message, to=[email])
            email.content_subtype = "html"
            email.send()
            return redirect("verify-email-done")
        else:
            return redirect("signup")
    return render(request, "verify-email.html")


def verify_email_done(request):
    return render(request, "verify-email-done.html")


def verify_email_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_email_verified = True
        user.save()
        messages.success(request, "Your email has been verified.")
        return redirect("verify-email-complete")
    else:
        messages.warning(request, "The link is invalid.")
    return render(request, "verify-email-confirm.html")


def verify_email_complete(request):
    return render(request, "verify-email-complete.html")


def signup_view(request):
    if request.method == "POST":
        print("signup POST request received\n")
        next_page = request.GET.get("next")
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get("password")
            user.set_password(password)
            user.save()
            new_user = authenticate(email=user.email, password=password)
            if new_user:
                login(request, new_user)
                return redirect("verify-email")
            else:
                print("Authentication failed")
            if next_page:
                return redirect(next_page)
            else:
                return redirect("verify-email")
        else:
            print("ERROR: Email already in use or passwords do not match\n")
    else:
        form = UserRegisterForm()
    context = {"form": form}
    return render(request, "signup.html", context)


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("/upload/")
    elif request.user.is_authenticated:
        return redirect("/upload/")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/upload/")


def upload_image(request):
    if request.method == "POST":
        image_form = forms.ImageForm(request.POST, request.FILES)
        if not request.user.is_authenticated:
            return redirect("/login/")
        elif image_form.is_valid():
            specimen_upload = SpecimenUpload()
            specimen_upload.user = request.user

            new_image = image_form.save(commit=False)
            new_image.specimen_upload = specimen_upload

            specimen_upload.save()
            new_image.save()
    else:
        image_form = forms.ImageForm()
    return render(request, "upload_photo.html", {"form": image_form})


def view_history(request):
    print(type(Image.objects.all()))

    images = Image.objects.none()
    if request.user.is_authenticated:
        for upload in SpecimenUpload.objects.filter(user=request.user):
            images = images | Image.objects.filter(specimen_upload=upload)
    return render(
        request, "history.html", {"images": images, "MEDIA_URL": settings.MEDIA_URL}
    )


def results_view(request):
    # Fetch known species and genus from the database
    species_results = list(KnownSpecies.objects.all().values("species_name", "resource_link", "confidence_level"))
    
    # Fetch the first genus (assuming there's only one, modify logic if needed)
    genus = Genus.objects.first()

    # Ensure genus appears at the top of the list
    if genus:
        species_results.insert(0, {"species_name": genus.genus_name, "resource_link": genus.resource_link, "confidence_level": genus.confidence_level})

    # Sort by confidence level (highest first)
    species_results.sort(key=lambda x: x["confidence_level"], reverse=True)

    # Get the most likely species (ignoring the genus)
    likely_species = species_results[1]["species_name"] if len(species_results) > 1 else "Unknown"

    # Dummy image URLs (replace with actual uploaded images if needed)
    image_urls = [
        "/static/images/sample1.jpg",
        "/static/images/sample2.jpg",
        "/static/images/sample3.jpg",
        "/static/images/sample4.jpg",
    ]

    return render(
        request,
        "results.html",
        {
            "species_results": species_results[:6],  # Ensure only 5 species + 1 genus are displayed
            "likely_species": likely_species,
            "image_urls": image_urls,
        },
    )
