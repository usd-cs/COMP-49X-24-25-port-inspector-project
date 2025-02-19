from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from .models import User, SpecimenUpload, Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token


User = get_user_model()  # noqa: F811


class EmailVerificationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="testuser@example.com", password="testpassword")
        self.user.is_email_verified = False
        self.user.save()

    def test_verify_email_view_sends_email(self):
        self.client.login(email="testuser@example.com", password="testpassword")
        response = self.client.post(reverse("verify-email"))
        self.assertEqual(response.status_code, 302)  # Redirect to verify-email-done
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify Email", mail.outbox[0].subject)

    def test_verify_email_confirm_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = account_activation_token.make_token(self.user)
        response = self.client.get(reverse("verify-email-confirm", args=[uid, token]))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertRedirects(response, reverse("verify-email-complete"))

    def test_verify_email_confirm_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(reverse("verify-email-confirm", args=[uid, "invalid-token"]))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)
        self.assertContains(response, "The link is invalid.")


class SignupTestCase(TestCase):
    def test_user_signup(self):
        response = self.client.post('/signup/', {  # Update URL as needed
            'email': 'test@example.com',
            'password': 'securepassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirects to 'verify-email' or 'next'
        user_exists = User.objects.filter(email='test@example.com').exists()
        self.assertTrue(user_exists)


class SpecimenUploadModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password123")

    def test_create_specimen_upload_with_images_valid(self):
        specimen_upload = SpecimenUpload.objects.create(user=self.user)
        image1 = Image.objects.create(
            specimen_upload=specimen_upload,
            image=SimpleUploadedFile("image1.jpg", b"file_content"),
        )
        image2 = Image.objects.create(
            specimen_upload=specimen_upload,
            image=SimpleUploadedFile("image2.jpg", b"file_content"),
        )
        self.assertEqual(specimen_upload.images.count(), 2)
        self.assertEqual(str(specimen_upload), f"SpecimenUpload #{specimen_upload.id} by {self.user.email} on {specimen_upload.upload_date}")
        self.assertEqual(str(image1), f"Image #{image1.id} for SpecimenUpload #{specimen_upload.id} uploaded at {image1.uploaded_at}")
        self.assertEqual(str(image2), f"Image #{image2.id} for SpecimenUpload #{specimen_upload.id} uploaded at {image2.uploaded_at}")

    def test_specimen_upload_images_too_few(self):
        specimen_upload = SpecimenUpload.objects.create(user=self.user)
        with self.assertRaises(ValidationError):
            specimen_upload.full_clean()

    def test_specimen_upload_images_too_many(self):
        specimen_upload = SpecimenUpload.objects.create(user=self.user)
        for i in range(6):
            Image.objects.create(
                specimen_upload=specimen_upload,
                image=SimpleUploadedFile(f"image{i}.jpg", b"file_content"),
            )
        with self.assertRaises(ValidationError):
            specimen_upload.full_clean()


class ImageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password123")
        self.specimen_upload = SpecimenUpload.objects.create(user=self.user)

    def test_image_creation(self):
        image = Image.objects.create(
            specimen_upload=self.specimen_upload,
            image=SimpleUploadedFile("image1.jpg", b"file_content"),
        )
        self.assertEqual(str(image), f"Image #{image.id} for SpecimenUpload #{self.specimen_upload.id} uploaded at {image.uploaded_at}")


class SpecimenUploadIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password123")

    def test_user_upload_workflow(self):
        # Create SpecimenUpload
        specimen_upload = SpecimenUpload.objects.create(user=self.user)

        # Add 3 images
        images = [
            Image.objects.create(
                specimen_upload=specimen_upload,
                image=SimpleUploadedFile(f"image{i}.jpg", b"file_content"),
            ) for i in range(3)
        ]

        # Validate SpecimenUpload
        specimen_upload.full_clean()
        # Check that each image filename starts with the expected prefix
        for i, img in enumerate(images):
            self.assertTrue(img.image.name.startswith(f"uploads/image{i}"))
