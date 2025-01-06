from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.admin import User
from accounts.models import Profile
from patients.models import Diagnosis, Patient
from jsonschema import validate


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = User.objects.create_user(
        email='doctor@test.com',
        password='testpass123',
    )
    profile = Profile.objects.create(
        user=user,
        full_name='Dr. Test Doctor',
        phone_number='+1234567890',
        specialization='Cardiology'
    )
    api_client.force_authenticate(user=user)
    return api_client, profile


@pytest.fixture
def sample_patient(authenticated_client):
    _, doctor_profile = authenticated_client
    return Patient.objects.create(
        doctor=doctor_profile,
        full_name='John Doe',
        date_of_birth=date(1990, 1, 1),
        gender='M',
        patient_id='P12345'
    )


@pytest.fixture
def sample_diagnosis(sample_patient):
    echo_file = SimpleUploadedFile(
        "test_echo.txt",
        b"test echo content",
        content_type="text/plain"
    )

    return Diagnosis.objects.create(
        patient=sample_patient,
        symptoms="Chest pain",
        view_type='a4c',
        echocardiogram=echo_file
    )


@pytest.mark.django_db
class TestAPIContracts:
    """Tests to ensure API responses match defined schemas"""

    def test_patient_list_schema(self, authenticated_client):
        client, _ = authenticated_client
        response = client.get('/api/patients/')

        # Schema definition of what we expect
        expected_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "full_name", "gender", "date_of_birth"],
                "properties": {
                    "id": {"type": "integer"},
                    "full_name": {"type": "string"},
                    "date_of_birth": {"type": "string", "format": "date"},
                    "patient_id": {"type": ["string", "null"]},
                    "gender": {"type": "string", "enum": ["M", "F"]},
                    "weight": {"type": ["number", "null"]},
                    "height": {"type": ["number", "null"]},
                    "phone_number": {"type": ["string", "null"]},
                    "address": {"type": ["string", "null"]}
                }
            }
        }

        # Validate response against schema
        validate(instance=response.data, schema=expected_schema)

    def test_diagnosis_detail_schema(self, authenticated_client, sample_diagnosis):
        client, _ = authenticated_client
        response = client.get(f'/api/patients/{sample_diagnosis.patient.id}/diagnoses/{sample_diagnosis.id}/')

        expected_schema = {
            "type": "object",
            "required": ["id", "patient", "diagnosis_date", "symptoms", "view_type"],
            "properties": {
                "id": {"type": "integer"},
                "patient": {"type": "integer"},
                "diagnosis_date": {"type": "string", "format": "date-time"},
                "symptoms": {"type": "string"},
                "view_type": {"type": "string", "enum": ["a4c", "psax"]},
                "prescription": {"type": "string"},
                "notes": {"type": "string"},
                "follow_up_date": {"type": ["string", "null"], "format": "date"},
                "ejection_fraction": {"type": ["number", "null"]},
                "echocardiogram": {"type": "string", "format": "uri"},
                "interpretations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "note", "created_at"],
                        "properties": {
                            "id": {"type": "integer"},
                            "note": {"type": "string"},
                            "created_at": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            }
        }

        validate(instance=response.data, schema=expected_schema)

    def test_profile_schema(self, authenticated_client):
        client, _ = authenticated_client
        response = client.get('/api/profile/')

        expected_schema = {
            "type": "object",
            "required": ["full_name", "phone_number", "specialization"],
            "properties": {
                "full_name": {"type": "string"},
                "phone_number": {"type": "string"},
                "specialization": {"type": "string"},
                "profile_picture": {"type": "string", "format": "uri"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"}
            }
        }

        validate(instance=response.data, schema=expected_schema)
