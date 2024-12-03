from django.db import models

# Create your models here.
class ImageSet(models.Model):
    upload_id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='')