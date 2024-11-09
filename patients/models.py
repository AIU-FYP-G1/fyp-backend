from django.db import models

from accounts.models import Profile


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female')
    ]

    doctor = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='patients')
    full_name = models.CharField(max_length=200, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class Diagnosis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_date = models.DateTimeField(auto_now_add=True)
    symptoms = models.TextField()
    diagnosis = models.TextField()
    prescription = models.TextField()
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    ef_prediction = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Diagnosis for {self.patient} on {self.diagnosis_date.date()}"
