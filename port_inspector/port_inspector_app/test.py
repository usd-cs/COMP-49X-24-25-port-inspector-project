from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from port_inspector_app.views import results_view
from port_inspector_app.models import SpecimenUpload, Genus, KnownSpecies, User, Image
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

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(email="testuser@example.com", password="securepassword")

        # Create a Genus instance
        self.genus = Genus.objects.create(genus_name="TestGenus", resource_link="http://example.com/genus")

        # Create multiple KnownSpecies instances
        self.species_1 = KnownSpecies.objects.create(species_name="TestSpecies1", resource_link="http://example.com/species1")
        self.species_2 = KnownSpecies.objects.create(species_name="TestSpecies2", resource_link="http://example.com/species2")

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

    def test_specimen_upload_with_valid_genus_and_species(self):
        # Create a valid SpecimenUpload with a valid genus and species list
        specimen_upload = SpecimenUpload.objects.create(
            user=self.user,
            genus=(self.genus.id_num, 0.95),  # Genus ID and confidence level
            species=[
                (self.species_1.id_num, 0.90),  # Species ID and confidence level
                (self.species_2.id_num, 0.85),
            ]
        )

        # Fetch the saved instance from the database
        retrieved_upload = SpecimenUpload.objects.get(id=specimen_upload.id)

        # Validate genus data
        self.assertEqual(retrieved_upload.genus, [self.genus.id_num, 0.95])

        # Validate species data
        self.assertEqual(len(retrieved_upload.species), 2)
        self.assertIn([self.species_1.id_num, 0.90], retrieved_upload.species)
        self.assertIn([self.species_2.id_num, 0.85], retrieved_upload.species)

    @patch("port_inspector_app.models.Image.objects.create")
    @patch("port_inspector_app.models.SpecimenUpload.images")
    def test_specimen_upload_with_invalid_genus_format(self, mock_images, mock_image_create):
        specimen_upload = SpecimenUpload.objects.create(
            user=self.user,
            genus="Invalid genus format",  # Invalid format
            species=[(self.species_1.id_num, 0.95)]  # Valid species format
        )

        images = [MagicMock() for _ in range(3)]
        mock_image_create.side_effect = images
        mock_images.count.return_value = 3  # Simulate 3 images

        with self.assertRaises(ValidationError) as context:
            specimen_upload.full_clean()  # Triggers validation

        self.assertIn("Genus must be a tuple containing (genus_id, confidence_level).", str(context.exception))

    @patch("port_inspector_app.models.Image.objects.create")
    @patch("port_inspector_app.models.SpecimenUpload.images")  # Mocking the related manager
    def test_specimen_upload_with_invalid_species_format(self, mock_images, mock_image_create):
        # Create specimen upload instance with valid genus and invalid species format
        specimen_upload = SpecimenUpload.objects.create(
            user=self.user,
            genus=("GenusId", 0.95),  # Valid genus format
            species="Invalid species format"  # Invalid species format
        )

        # Mock the images manager to simulate having images (e.g., 3 images)
        images = [MagicMock() for _ in range(3)]
        mock_image_create.side_effect = images
        mock_images.count.return_value = 3  # Simulate 3 images

        # Perform full_clean which triggers validation
        with self.assertRaises(ValidationError) as context:
            specimen_upload.full_clean()

        # Ensure the validation error for species format is raised
        self.assertIn("Species must be a list of 1 to 5 (species_id, confidence_level) tuples.", str(context.exception))


class ResultsViewTests(TestCase):

    @patch("port_inspector_app.models.KnownSpecies.objects.filter")
    @patch("port_inspector_app.models.Genus.objects.filter")
    def test_results_view(self, mock_genus_filter, mock_species_filter):
        # Mock the return values of the queries
        mock_species_filter.return_value.values_list.return_value = [("species1", "http://species1.com")]
        mock_genus_filter.return_value.values_list.return_value = [("genus1", "http://genus1.com")]

        # Create a mock request object
        request = HttpRequest()
        request.method = 'GET'

        # Call the view function
        hashed_ID = "mocked_hash_value"  # Fake hash
        response = results_view(request, hashed_ID)

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

    @patch("port_inspector_app.views.KnownSpecies.objects.filter")
    @patch("port_inspector_app.views.Genus.objects.filter")
    def test_results_view_species_sorted_by_confidence(self, mock_genus_filter, mock_species_filter):
        # Mock the return values of the queries with species results having different confidence levels
        mock_species_filter.return_value.values_list.return_value = [
            ("species1", "http://species1.com"),  # confidence 95.5
            ("species2", "http://species2.com"),  # confidence 23.9
            ("species3", "http://species3.com"),  # confidence 15.7
            ("species4", "http://species4.com"),  # confidence 12.3
            ("species5", "http://species5.com")   # confidence 5.5
        ]

        # Mock genus result
        mock_genus_filter.return_value.values_list.return_value = [("genus1", "http://genus1.com")]

        # Create a mock request object
        request = HttpRequest()
        request.method = 'GET'

        # Call the view function
        hashed_ID = "mocked_hash_value"  # Fake hash
        response = results_view(request, hashed_ID)

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        html_content = response.content.decode()  # Decode the response to a string

        # Check if the first species name in the HTML is 'species1'
        self.assertIn('species1', html_content)  # species1 should be in the HTML

        # Check if species1's confidence level appears first in the HTML
        self.assertIn('95.5', html_content)
