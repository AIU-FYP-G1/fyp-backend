import random

import requests
from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from patients.models import Patient, Diagnosis, Interpretation
from patients.serializers import PatientSerializer, DiagnosisSerializer


class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return patients associated with the logged-in doctor's profile
        return Patient.objects.filter(doctor=self.request.user.profile)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.profile)


class PatientDetailView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(doctor=self.request.user.profile)


class DiagnosisListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    ECHO_ANALYSIS_URL = 'empty_for_now'

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return Diagnosis.objects.filter(
            patient_id=patient_id,
            patient__doctor=self.request.user.profile
        ).prefetch_related('interpretations').order_by('-diagnosis_date')

    def perform_create(self, serializer):
        patient_id = self.kwargs.get('patient_id')
        patient = Patient.objects.get(id=patient_id, doctor=self.request.user.profile)

        diagnosis = serializer.save(patient=patient)

        self.create_fake_interpretations(diagnosis)

        try:
            self.analyze_echo(diagnosis)
        except Exception as e:
            print(f"Error analyzing echo: {str(e)}")

    def create_fake_interpretations(self, diagnosis):
        num_interpretations = random.randint(2, 3)
        fake_interpretations = [
            "Normal sinus rhythm with no significant abnormalities",
            "Mild left ventricular hypertrophy noted",
            "Trace mitral regurgitation present",
            "Normal systolic function with preserved ejection fraction",
            "Minor wall motion abnormalities in inferior wall"
        ]

        for i in range(num_interpretations):
            interpretation = random.choice(fake_interpretations)
            Interpretation.objects.create(
                diagnosis=diagnosis,
                note=interpretation
            )

    def analyze_echo(self, diagnosis):
        try:
            # files = {'file': diagnosis.echocardiogram.open()}

            # response = requests.post(self.ECHO_ANALYSIS_URL, files=files)
            # response.raise_for_status()
            #
            # analysis_results = response.json()

            # diagnosis.ejection_fraction = analysis_results.get('ejection_fraction')
            placeholder_ef_value = random.randint(50, 100)
            diagnosis.ejection_fraction = placeholder_ef_value
            diagnosis.save()

        finally:
            diagnosis.echocardiogram.close()


class DiagnosisDetailView(generics.RetrieveAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return Diagnosis.objects.filter(
            patient_id=patient_id,
            patient__doctor=self.request.user.profile)
