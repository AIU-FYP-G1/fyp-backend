# Generated by Django 5.1.2 on 2024-11-03 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='last_name',
        ),
        migrations.AddField(
            model_name='profile',
            name='full_name',
            field=models.CharField(default='', max_length=200),
        ),
    ]
