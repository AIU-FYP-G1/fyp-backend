from rest_framework import serializers

from patients.models import Patient, Diagnosis


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class DiagnosisSerializer(serializers.ModelSerializer):
    echocardiogram = serializers.FileField(required=True)
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    diagnosis_date = serializers.DateTimeField(format="%Y-%m-%d**%H:%M:%S", required=False)

    class Meta:
        model = Diagnosis
        fields = '__all__'
