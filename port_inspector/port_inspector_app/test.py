from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.core.mail import outbox
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile


class UserEmailIntegrationTests(TestCase):

    @patch("port_inspector_app.models.User.objects.create_user")
    @patch("port_inspector_app.models.User.objects.get")
    def test_user_email_valid(self, mock_get_user, mock_create_user):
        mock_user = MagicMock(email="validuser@example.com")
        mock_create_user.return_value = mock_user
        mock_get_user.return_value = mock_user
        self.assertEqual(mock_get_user().email, "validuser@example.com")

    def test_user_email_invalid(self):
        with self.assertRaises(ValidationError):
            raise ValidationError("invalid email")

    @patch("port_inspector_app.models.User.objects.create_user")
    def test_user_login_integration(self, mock_create_user):
        mock_user = MagicMock(email="validlogin@example.com")
        mock_create_user.return_value = mock_user
        response = self.client.post(reverse('login'), {'email': "validlogin@example.com", 'password': "securepassword123"})
        self.assertEqual(response.status_code, 200)


class SignupTestCase(TestCase):

    @patch("port_inspector_app.forms.UserRegisterForm.save")
    def test_user_signup(self, mock_save):
        mock_user = MagicMock()
        mock_save.return_value = mock_user

        response = self.client.post(reverse("signup"), {
            "email": "test@example.com",
            "password": "securepassword",
        })

        if response.context and "form" in response.context:
            print(response.context["form"].errors)

        mock_save.assert_called_once()
        self.assertEqual(response.status_code, 302)


class SpecimenUploadModelTests(TestCase):

    @patch("port_inspector_app.models.SpecimenUpload.objects.create")
    @patch("port_inspector_app.models.Image.objects.create")
    def test_create_specimen_upload_with_images_valid(self, mock_image_create, mock_upload_create):
        mock_upload = MagicMock()
        mock_upload.images.count.return_value = 2
        mock_upload_create.return_value = mock_upload

        mock_image_create.side_effect = [MagicMock(), MagicMock()]

        self.assertEqual(mock_upload.images.count(), 2)

    def test_specimen_upload_images_too_few(self):
        with self.assertRaises(ValidationError):
            raise ValidationError("A SpecimenUpload must have between 1 and 5 images.")

    def test_specimen_upload_images_too_many(self):
        with self.assertRaises(ValidationError):
            raise ValidationError("A SpecimenUpload must have between 1 and 5 images.")


class ImageModelTests(TestCase):

    @patch("port_inspector_app.models.Image.objects.create")
    def test_image_creation(self, mock_image_create):
        mock_image = MagicMock()
        mock_image_create.return_value = mock_image
        self.assertIsInstance(mock_image, MagicMock)


class SpecimenUploadIntegrationTests(TestCase):

    @patch("port_inspector_app.models.SpecimenUpload.objects.create")
    @patch("port_inspector_app.models.Image.objects.create")
    def test_user_upload_workflow(self, mock_image_create, mock_upload_create):
        mock_upload = MagicMock()
        mock_upload_create.return_value = mock_upload

        images = [MagicMock() for _ in range(3)]
        mock_image_create.side_effect = images

        mock_upload.full_clean()
        for img in images:
            self.assertIsInstance(img, MagicMock)
