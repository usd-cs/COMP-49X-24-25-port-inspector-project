from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from port_inspector_app.models import Image, SpecimenUpload, KnownSpecies, Genus
from . import forms
from .forms import UserRegisterForm, SpecimenUploadForm
from .tokens import account_activation_token

User = get_user_model()


# Handle email verification

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


# Sign-up new user

def signup_view(request):
    if request.method == "POST":
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
            if next_page:
                return redirect(next_page)
            else:
                return redirect("verify-email")
    else:
        form = UserRegisterForm()
    return render(request, "signup.html", {"form": form})


# Login view

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


# Logout view

def logout_view(request):
    logout(request)
    return redirect("/upload/")


# Upload view (submit specimen)

def upload_image(request):
    if request.method == "POST":
        specimen_form = SpecimenUploadForm(request.POST, request.FILES)

        if not request.user.is_authenticated:
            return redirect("/login/")

        elif specimen_form.is_valid():
            specimen_form.save(user=request.user)
            return redirect("/history/")

    else:
        specimen_form = SpecimenUploadForm()

    return render(request, 'upload_photo.html', {'form': specimen_form})


# History view

def view_history(request):
    if request.user.is_authenticated:
        uploads = SpecimenUpload.objects.filter(user=request.user)
        return render(request, 'history.html', {'uploads': uploads, 'MEDIA_URL': settings.MEDIA_URL})
    else:
        return redirect("/login/")


# Results page (mock data from BeetleID team for now)

def results_view(request):
    # This data comes from the BeetleID team
    species_results = [
        ("species1", 95.5), ("species2", 23.9), ("species3", 15.7),
        ("species4", 12.3), ("species5", 5.5)
    ]
    genus_result = ("genus1", 92.4)

    # Fetch species URLs from the database
    species_names = [species[0] for species in species_results]
    species_data = KnownSpecies.objects.filter(species_name__in=species_names).values_list("species_name", "resource_link")
    species_dict = dict(species_data)

    # Fetch genus URL from the database
    genus_name = genus_result[0]
    genus_data = Genus.objects.filter(genus_name=genus_name).values_list("genus_name", "resource_link")
    genus_dict = dict(genus_data)

    # Build species results with URLs
    formatted_species_results = [
        {
            "species_name": species[0],
            "confidence_level": species[1],
            "resource_link": species_dict.get(species[0], "#"),
        }
        for species in species_results
    ]

    # Include the genus at the top
    if genus_dict:
        formatted_species_results.insert(0, {
            "species_name": genus_name,
            "confidence_level": genus_result[1],
            "resource_link": genus_dict.get(genus_name, "#"),
        })

    # Sort by confidence level (highest first)
    formatted_species_results.sort(key=lambda x: x["confidence_level"], reverse=True)

    # Determine the most likely species (excluding genus)
    likely_species = formatted_species_results[1]["species_name"] if len(formatted_species_results) > 1 else "Unknown"

    # Dummy image URLs (replace with actual uploaded images if needed)
    image_urls = [
        "/static/images/sample1.jpg",
        "/static/images/sample2.jpg",
        "/static/images/sample3.jpg",
        "/static/images/sample4.jpg",
    ]

    # All known species for dropdown
    all_species = KnownSpecies.objects.all()

    return render(
        request,
        "results.html",
        {
            "species_results": formatted_species_results[:6],
            "likely_species": likely_species,
            "image_urls": image_urls,
            "known_species": all_species,
        },
    )


# Confirm button AJAX view

@require_POST
@csrf_exempt
def confirm_species(request):
    species_name = request.POST.get("confirmed_species")
    if species_name:
        print(f"Confirmed species: {species_name}")
        return JsonResponse({"message": f"Species '{species_name}' confirmed!"}, status=200)
    return JsonResponse({"error": "No species provided."}, status=400)


# Notify Dr. Morse for unknown species

@require_POST
@csrf_exempt
def notify_unknown(request):
    try:
        send_mail(
            subject="Unknown Species Notification",
            message="A user has reported an unknown species in the system.",
            from_email="noreply@portinspector.com",
            recipient_list=["dr.morse@example.com"],
            fail_silently=False,
        )
        return JsonResponse({"message": "Notification sent to Dr. Morse."}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
