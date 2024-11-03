from rest_framework import generics, permissions

from patients.models import Patient, Diagnosis
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

    def get_queryset(self):
        # Get the patient ID from URL parameters
        patient_id = self.kwargs.get('patient_id')
        return Diagnosis.objects.filter(patient_id=patient_id, patient__doctor=self.request.user.profile)

    def perform_create(self, serializer):
        patient_id = self.kwargs.get('patient_id')
        patient = Patient.objects.get(id=patient_id, doctor=self.request.user.profile)
        serializer.save(patient=patient)


class DiagnosisDetailView(generics.RetrieveAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return Diagnosis.objects.filter(
            patient_id=patient_id,
            patient__doctor=self.request.user.profile)
