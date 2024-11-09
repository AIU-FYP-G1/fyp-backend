from rest_framework import serializers

from patients.models import Patient, Diagnosis


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class DiagnosisSerializer(serializers.ModelSerializer):
    echocardiogram = serializers.FileField(required=True)

    class Meta:
        model = Diagnosis
        fields = '__all__'
        read_only_fields = 'ejection_fraction'