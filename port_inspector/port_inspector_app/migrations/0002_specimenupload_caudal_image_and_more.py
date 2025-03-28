# Generated by Django 4.2.16 on 2025-03-21 01:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('port_inspector_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='specimenupload',
            name='caudal_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='caudal_image', to='port_inspector_app.image'),
        ),
        migrations.AddField(
            model_name='specimenupload',
            name='dorsal_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dorsal_image', to='port_inspector_app.image'),
        ),
        migrations.AddField(
            model_name='specimenupload',
            name='frontal_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='frontal_image', to='port_inspector_app.image'),
        ),
        migrations.AddField(
            model_name='specimenupload',
            name='lateral_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lateral_image', to='port_inspector_app.image'),
        ),
    ]
