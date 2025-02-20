from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import User, SpecimenUpload, Image
from django.core.files.uploadedfile import SimpleUploadedFile
# flake8: noqa

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

class UserEmailIntegrationTests(TestCase):
    def test_user_email_valid(self):
        # Test creating a user with a valid email
        valid_email = "validuser@example.com"
        user = User.objects.create_user(email=valid_email, password="securepassword123")
        user.full_clean()  # Should not raise an error
        
        # Verify user was saved correctly
        retrieved_user = User.objects.get(email=valid_email)
        self.assertEqual(retrieved_user.email, valid_email)

    def test_user_email_invalid(self):
        # Test creating a user with an invalid email
        invalid_email = "invaliduser"
        user = User(email=invalid_email, password="securepassword123")
        
        with self.assertRaises(ValidationError):
            user.full_clean()  # Should raise ValidationError due to invalid email format

