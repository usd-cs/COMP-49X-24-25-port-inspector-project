from django.shortcuts import render, redirect
from django.conf import settings
from beetle_detection import species_eval
from port_inspector_app.models import Image, SpecimenUpload, User, KnownSpecies, Genus
from .forms import UserRegisterForm, SpecimenUploadForm, ConfirmIdForm
from django.core import signing
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from .tokens import account_activation_token


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
        return redirect("/login/")
    else:
        messages.warning(request, "The link is invalid.")
    return render(request, "verify-email-confirm.html")


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
            return redirect("/upload/")  # after the user logs in, send them to the homepage
    # if user is already logged in, redirect
    elif request.user.is_authenticated:
        return redirect("/upload/")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


# log the user out and send them back to the upload page
def logout_view(request):
    logout(request)
    return redirect("/upload/")


def upload_image(request):
    if request.method == "POST":
        specimen_form = SpecimenUploadForm(request.POST, request.FILES)

        if not request.user.is_authenticated:
            return redirect("/login/")

        elif specimen_form.is_valid():
            specimen = specimen_form.save(user=request.user)
            hashed_ID = signing.dumps(specimen.id, salt=settings.SALT_KEY)
            return redirect("results", hashed_ID=hashed_ID)  # go to a UNIQUE URL for the results

    else:
        specimen_form = SpecimenUploadForm()

    return render(request, 'upload_photo.html', {'form': specimen_form})


def view_history(request):
    if request.user.is_authenticated:
        # create empty set of type SpecimenUpload
        specimen = SpecimenUpload.objects.filter(user=request.user).order_by('-upload_date')
        uploads = []
        for upload in specimen:
            hashed_ID = signing.dumps(upload.id, salt=settings.SALT_KEY)
            uploads.append((upload, hashed_ID))
        return render(request, 'history.html', {'uploads': uploads, 'max_uploads': settings.USER_MAX_UPLOADS})
    else:
        return redirect("/login/")


def results_view(request, hashed_ID):
    try:
        upload_id = signing.loads(hashed_ID, salt=settings.SALT_KEY)
        upload = SpecimenUpload.objects.get(id=upload_id)
    except (SpecimenUpload.DoesNotExist, signing.BadSignature):
        # Invalid id/Upload does not exist
        upload_id, upload = None, None

    # If SpecimenUpload has not been evaluated yet, evaluate and store in db
    if upload:
        if upload.genus[0] is None and upload.species[0][0] is None:
            lat_image = upload.lateral_image.image if upload.lateral_image else None
            dor_image = upload.dorsal_image.image if upload.dorsal_image else None
            fron_image = upload.frontal_image.image if upload.frontal_image else None
            caud_image = upload.caudal_image.image if upload.caudal_image else None

            s, g = species_eval.evaluate_images(lat_image, dor_image, fron_image, caud_image)

            upload.species = s
            upload.genus = g
            upload.save()

        # Get ML results from the db
        species_results = upload.species
        genus_result = upload.genus
    else:
        species_results = [(None, None)]
        genus_result = (None, None)

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
            "resource_link": species_dict.get(species[0], "#"),  # Default to "#" if not found
        }
        for species in species_results
    ]

    # Sort by confidence level (highest first)
    formatted_species_results.sort(key=lambda x: x["confidence_level"], reverse=True)

    # Include the genus at the top
    formatted_species_results.insert(0, {
        "species_name": genus_name,
        "confidence_level": genus_result[1],
        "resource_link": genus_dict.get(genus_name, "#"),
    })

    # Determine the most likely species (excluding genus)
    likely_species = formatted_species_results[1]["species_name"] if len(formatted_species_results) > 1 else "Unknown"

    image_urls = ["", "", "", ""]
    if upload:
        image_urls[0] = upload.frontal_image.image if upload.frontal_image is not None else "default_image.jpg"
        image_urls[1] = upload.dorsal_image.image if upload.dorsal_image is not None else "default_image.jpg"
        image_urls[2] = upload.caudal_image.image if upload.caudal_image is not None else "default_image.jpg"
        image_urls[3] = upload.lateral_image.image if upload.lateral_image is not None else "default_image.jpg"

    confirm_choices = [(name, name) for name in species_names] + [("Other", "Other")]

    # Confirm species form
    if request.method == "POST":
        confirm_form = ConfirmIdForm(request.POST, choices=confirm_choices)
        if confirm_form.is_valid():
            upload.final_identification = confirm_form.cleaned_data['choice']
            upload.save()  # Save new data to the database
            # TODO add some form of confirmation here
            print("IDENTIFIED AS: ", upload.final_identification)
    else:
        confirm_form = ConfirmIdForm(choices=confirm_choices)

    confirmed_species = upload.final_identification if upload else None

    return render(
        request,
        "results.html",
        {
            "species_results": formatted_species_results[:6],  # Ensure only 5 species + 1 genus are displayed
            "upload_id": upload.id if upload else "DELETED",
            "likely_species": likely_species,
            "confirmed_species": confirmed_species,
            "image_urls": image_urls,
            "confirm_form": confirm_form
        },
    )


def notify_unknown(request):
    if request.method == "POST":
        user = request.user
        if user.is_usda:
            send_to_email = "usdportinspector@gmail.com"
            results_page_url = request.META.get("HTTP_REFERER", "/history/")
            subject = "Port Inspector App - Unknown Species Uploaded"
            message = f"""
            <p>Hello,</p>
            <p>A user was unable to identify a specimen.</p>
            <p>Confirm the identification here: <a href="{results_page_url}">{results_page_url}</a></p>
            <p>Best,</p>
            <p>Port Inspector App Team</p>
            """
            email = EmailMessage(subject, message, to=[send_to_email])
            email.content_subtype = "html"
            email.send()

    return redirect("/history/")
