from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import User, SpecimenUpload, Image
from django.core.files.uploadedfile import SimpleUploadedFile

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
