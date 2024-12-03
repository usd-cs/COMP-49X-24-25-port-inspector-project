from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Custom related_name to avoid clash
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # Custom related_name to avoid clash
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class SpecimenUpload(models.Model):
    id = models.AutoField(primary_key=True)  # Explicit primary key
    user = models.ForeignKey('port_inspector_app.User', on_delete=models.CASCADE, related_name="uploads")
    upload_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Perform validation after saving
        num_images = self.images.count()
        if num_images < 1 or num_images > 5:
            raise ValidationError(f"A SpecimenUpload must have between 1 and 5 images. Found {num_images}.")
            
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"SpecimenUpload #{self.id} by {self.user.email} on {self.upload_date}"

class Image(models.Model):
    id = models.AutoField(primary_key=True)  # Explicit primary key
    specimen_upload = models.ForeignKey('port_inspector_app.SpecimenUpload', on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image #{self.id} for SpecimenUpload #{self.specimen_upload.id} uploaded at {self.uploaded_at}"
