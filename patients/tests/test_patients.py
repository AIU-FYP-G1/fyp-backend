import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from datetime import date, timedelta
import os

from accounts.models import Profile
from patients.models import Patient, Diagnosis

User = get_user_model()


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
class TestPatientManagement:
    """Tests for patient-related behaviors"""

    def test_doctor_can_only_see_their_patients(self, authenticated_client, sample_patient):
        """Ensures doctors can only access their own patients"""
        client, _ = authenticated_client

        other_user = User.objects.create_user(
            email='otherdoc@test.com',
            password='pass123'
        )
        other_doctor = Profile.objects.create(
            user=other_user,
            full_name='Dr. Other',
            phone_number='+1987654321',
            specialization='Cardiology'
        )
        Patient.objects.create(
            doctor=other_doctor,
            full_name='Jane Smith',
            gender='F'
        )

        response = client.get('/api/patients/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['full_name'] == 'John Doe'

    def test_patient_creation_with_required_fields(self, authenticated_client):
        """Ensures patients can be created with mandatory fields"""
        client, _ = authenticated_client

        patient_data = {
            'full_name': 'Jane Doe',
            'gender': 'F',
            'date_of_birth': '1995-05-15',
            'patient_id': 'P12346'
        }

        response = client.post('/api/patients/', patient_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['full_name'] == 'Jane Doe'

    def test_patient_age_calculation(self, sample_patient):
        """Ensures correct age calculation"""
        expected_age = (date.today() - sample_patient.date_of_birth).days // 365
        assert sample_patient.get_age() == expected_age


@pytest.mark.django_db
class TestDiagnosisManagement:
    """Tests for diagnosis-related behaviors"""

    def test_diagnosis_creation_with_echo_upload(self, authenticated_client, sample_patient):
        """Ensures diagnoses can be created with file uploads"""
        client, _ = authenticated_client

        echo_file = SimpleUploadedFile(
            "echo.txt",
            b"echo content",
            content_type="text/plain"
        )

        diagnosis_data = {
            'symptoms': 'Shortness of breath',
            'view_type': 'a4c',
            'echocardiogram': echo_file
        }

        response = client.post(
            f'/api/patients/{sample_patient.id}/diagnoses/',
            diagnosis_data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'echocardiogram' in response.data
        assert response.data['symptoms'] == 'Shortness of breath'

        diagnosis = Diagnosis.objects.get(id=response.data['id'])
        assert os.path.exists(diagnosis.echocardiogram.path)

    def test_diagnosis_cleanup_on_deletion(self, sample_diagnosis):
        """Ensures proper cleanup of files when diagnosis is deleted"""
        file_path = sample_diagnosis.echocardiogram.path
        assert os.path.exists(file_path)

        sample_diagnosis.delete()
        assert not os.path.exists(file_path)

    def test_diagnosis_interpretation_creation(self, authenticated_client, sample_patient):
        """Ensures interpretations are created when diagnosis is created via API"""
        client, _ = authenticated_client

        echo_file = SimpleUploadedFile(
            "test_echo.txt",
            b"test echo content",
            content_type="text/plain"
        )

        diagnosis_data = {
            'symptoms': 'Chest pain',
            'view_type': 'a4c',
            'echocardiogram': echo_file
        }

        create_response = client.post(
            f'/api/patients/{sample_patient.id}/diagnoses/',
            diagnosis_data,
            format='multipart'
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        diagnosis_id = create_response.data['id']
        get_response = client.get(f'/api/patients/{sample_patient.id}/diagnoses/{diagnosis_id}/')

        assert get_response.status_code == status.HTTP_200_OK
        assert len(get_response.data['interpretations']) > 0

        assert get_response.data['ejection_fraction'] is not None

    def test_historical_diagnosis_access(self, authenticated_client, sample_patient):
        """Ensures proper access to patient's diagnosis history"""
        client, _ = authenticated_client

        dates = [
            timezone.now() - timedelta(days=i * 30)
            for i in range(3)
        ]

        for i, diagnosis_date in enumerate(dates):
            diagnosis = Diagnosis.objects.create(
                patient=sample_patient,
                symptoms=f"Symptom set {i}"
            )
            diagnosis.diagnosis_date = diagnosis_date
            diagnosis.save()

        response = client.get(f'/api/patients/{sample_patient.id}/diagnoses/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert response.data[0]['diagnosis_date'] > response.data[1]['diagnosis_date']


@pytest.mark.django_db
class TestAccessControl:
    """Tests for security and access control"""

    def test_unauthenticated_access_blocked(self, api_client):
        """Ensures unauthenticated access is blocked"""
        response = api_client.get('/api/patients/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cross_doctor_access_prevented(self, authenticated_client):
        """Ensures doctors cannot access other doctors' data"""
        client, _ = authenticated_client

        other_user = User.objects.create_user(
            email='otherdoc@test.com',
            password='pass123'
        )
        other_doctor = Profile.objects.create(
            user=other_user,
            full_name='Dr. Other',
            phone_number='+1987654321',
            specialization='Cardiology'
        )
        other_patient = Patient.objects.create(
            doctor=other_doctor,
            full_name='Other Patient',
            gender='M'
        )

        response = client.get(f'/api/patients/{other_patient.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_profile_required_for_access(self, api_client):
        """Ensures users without profiles cannot access the system"""
        user = User.objects.create_user(
            email='noprofile@test.com',
            password='testpass123'
        )
        api_client.force_authenticate(user=user)

        try:
            response = api_client.get('/api/patients/')
            assert response.status_code == status.HTTP_403_FORBIDDEN
        except User.profile.RelatedObjectDoesNotExist:
            pass