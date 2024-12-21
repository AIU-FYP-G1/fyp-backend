import random

import numpy as np
import pandas as pd
from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from patients.prediction.EFPredictor import EFPredictionPipeline
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

            default_view = 'a4c'

            pipeline = EFPredictionPipeline(view=default_view)

            demo_data = {
                'age': 65,
                'sex': 1,
                'weight': 70,
                'height': 170,
            }

            volume_tracings = pd.DataFrame({
                'X': np.random.normal(100, 10, 100),
                'Y': np.random.normal(100, 10, 100)
            })

            ejection_fraction = pipeline.predict_ef(diagnosis.echocardiogram, demo_data, volume_tracings)

            diagnosis.ejection_fraction = ejection_fraction
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
