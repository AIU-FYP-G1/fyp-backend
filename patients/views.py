import json
import os
import random
import time

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

        try:
            self.analyze_echo(diagnosis)
        except Exception as e:
            print(f"Error analyzing echo: {str(e)}")

        self.create_interpretations(diagnosis)

    def create_interpretations(self, diagnosis):
        ef = diagnosis.ejection_fraction

        if ef >= 75:
            interpretations = [
                "Dangerously elevated ejection fraction (≥75%) suggesting possible Hypertrophic Cardiomyopathy",
                "High risk condition requiring immediate attention due to potential cardiac arrest risk",
                "Impaired ventricular filling due to extremely high ejection fraction"
            ]
        elif 50 <= ef <= 70:
            interpretations = [
                f"Normal ejection fraction ({ef}%) indicating preserved systolic function",
                "Heart pumping function within normal range",
                "Consider monitoring for HFpEF despite normal ejection fraction"
            ]
        elif 41 <= ef <= 49:
            interpretations = [
                f"Borderline low ejection fraction ({ef}%) indicating mild systolic dysfunction",
                "May experience mild symptoms during physical activity",
                "Regular monitoring and follow-up recommended"
            ]
        elif 30 <= ef <= 40:
            interpretations = [
                f"Moderately abnormal ejection fraction ({ef}%) indicating significant dysfunction",
                "Patient may experience symptoms even at rest",
                "Close monitoring and therapy adjustment may be needed"
            ]
        else:  # ef < 30
            interpretations = [
                f"Severely abnormal ejection fraction ({ef}%) indicating critical cardiac dysfunction",
                "High risk condition requiring immediate medical attention",
                "Patient likely experiencing severe symptoms with risk of cardiac arrest"
            ]

        num_interpretations = random.randint(2, 3)
        selected_interpretations = random.sample(interpretations, num_interpretations)

        for interpretation in selected_interpretations:
            Interpretation.objects.create(
                diagnosis=diagnosis,
                note=interpretation
            )

    def analyze_echo(self, diagnosis):
        try:
            API_URL = "https://fe60-124-13-17-173.ngrok-free.app/predict"

            files = {
                'video': diagnosis.echocardiogram.file
            }

            demo_data = {
                'age': diagnosis.patient.get_age(),
                'weight': diagnosis.patient.weight if diagnosis.patient.weight else 70,
                'height': diagnosis.patient.height if diagnosis.patient.height else 180,
            }

            data = {
                'view': diagnosis.view_type,
                'demographic_data': json.dumps(demo_data),
            }

            # diagnosis.ejection_fraction = self.get_random_ef()
            # diagnosis.save()

            response = requests.post(API_URL, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                diagnosis.ejection_fraction = result['ef_prediction']
                diagnosis.save()
            else:
                error_message = response.json().get('detail', 'Unknown error')
                raise Exception(f"API Error: {error_message}")

        except requests.RequestException as e:
            print(f"Error calling inference API: {str(e)}")
            raise
        except Exception as e:
            print(f"Error in analyze_echo: {str(e)}")
            raise
        finally:
            diagnosis.echocardiogram.close()

    def get_random_ef(self):
        time.sleep(4)
        weights = [
            (55, 70, 50),
            (40, 54, 25),
            (71, 90, 15),
            (10, 39, 10)
        ]

        chosen_range = random.choices(weights, weights=[w[2] for w in weights])[0]
        return random.randint(chosen_range[0], chosen_range[1])


class DiagnosisDetailView(generics.RetrieveAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return Diagnosis.objects.filter(
            patient_id=patient_id,
            patient__doctor=self.request.user.profile)
