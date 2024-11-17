from rest_framework import serializers

from patients.models import Patient, Diagnosis, Interpretation


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class InterpretationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interpretation
        fields = ['id', 'note', 'created_at']


class DiagnosisSerializer(serializers.ModelSerializer):
    interpretations = InterpretationSerializer(many=True, read_only=True)
    echocardiogram = serializers.FileField(required=True)
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    diagnosis_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    class Meta:
        model = Diagnosis
        fields = '__all__'
