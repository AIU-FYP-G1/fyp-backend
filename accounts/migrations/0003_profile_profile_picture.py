# Generated by Django 5.1.2 on 2024-11-15 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_remove_profile_first_name_remove_profile_last_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='profile_picture',
            field=models.FileField(default='profiles/default-avatar.jpg', upload_to='profiles/'),
        ),
    ]
