import os

from django.db import models

from accounts.models import Profile


def echo_upload_path(instance, filename):
    return f'echos/patient_{instance.patient.id}/{instance.diagnosis_date.strftime("%Y-%m-%d")}_{filename}'


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female')
    ]

    doctor = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='patients')
    full_name = models.CharField(max_length=200, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_age(self):
        if self.date_of_birth:
            return (self.date_of_birth.today() - self.date_of_birth).days // 365
        else:
            return 0

    def __str__(self):
        return self.full_name


class Diagnosis(models.Model):
    VIEW_CHOICES = [
        ('a4c', 'A4C'),
        ('psax', 'PSAX'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_date = models.DateTimeField(auto_now_add=True)
    symptoms = models.TextField(default='')
    view_type = models.CharField(max_length=100, choices=VIEW_CHOICES, default='a4c')
    prescription = models.TextField(default='')
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    ejection_fraction = models.FloatField(null=True, blank=True, default=0)
    echocardiogram = models.FileField(upload_to=echo_upload_path, default='')

    def __str__(self):
        return f"Diagnosis for {self.patient} on {self.diagnosis_date.date()}"

    def delete(self, *args, **kwargs):
        if self.echocardiogram:
            if os.path.isfile(self.echocardiogram.path):
                os.remove(self.echocardiogram.path)
        super().delete(*args, **kwargs)


class Interpretation(models.Model):
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, related_name='interpretations')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interpretation for {self.diagnosis} - {self.created_at}"
