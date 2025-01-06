import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from accounts.models import Profile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAuthentication:
    """Tests for user registration and authentication"""

    def test_user_signup_successful(self, api_client):
        """Ensures users can register with valid data"""
        signup_data = {
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'full_name': 'Test User',
            'phone_number': '+1234567890',
            'specialization': 'Cardiology'
        }

        response = api_client.post('/api/signup/', signup_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'message' in response.data

        # Verify profile was created
        user = User.objects.get(email=signup_data['email'])
        assert hasattr(user, 'profile')
        assert user.profile.full_name == signup_data['full_name']

    def test_user_login_successful(self, api_client):
        """Ensures users can login with correct credentials"""
        # Create user first
        user_data = {
            'email': 'testuser@test.com',
            'password': 'testpass123'
        }
        User.objects.create_user(**user_data)

        response = api_client.post('/api/login/', user_data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_invalid_login_credentials(self, api_client):
        """Ensures login fails with incorrect credentials"""
        response = api_client.post('/api/login/', {
            'email': 'wrong@test.com',
            'password': 'wrongpass'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProfileManagement:
    """Tests for profile management"""

    @pytest.fixture
    def authenticated_user(self, api_client):
        user = User.objects.create_user(
            email='testuser@test.com',
            password='testpass123'
        )
        Profile.objects.create(
            user=user,
            full_name='Test User',
            phone_number='+1234567890',
            specialization='Cardiology'
        )

        api_client.force_authenticate(user=user)
        return api_client, user

    def test_profile_update_successful(self, authenticated_user):
        """Ensures users can update their profile information"""
        client, _ = authenticated_user

        update_data = {
            'full_name': 'Updated Name',
            'phone_number': '+9876543210',
            'specialization': 'Pediatrics'
        }

        response = client.patch('/api/profile/', update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['full_name'] == update_data['full_name']
        assert response.data['specialization'] == update_data['specialization']

    def test_profile_picture_update(self, authenticated_user):
        """Ensures profile picture can be updated"""
        client, _ = authenticated_user

        # Create a test image file
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )

        response = client.patch(
            '/api/profile/',
            {'profile_picture': image},
            format='multipart'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'profile_picture' in response.data
        assert 'default-avatar' not in response.data['profile_picture']

    def test_profile_get_successful(self, authenticated_user):
        """Ensures users can retrieve their profile information"""
        client, user = authenticated_user

        response = client.get('/api/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['full_name'] == user.profile.full_name


@pytest.mark.django_db
class TestPasswordManagement:
    """Tests for password management"""

    @pytest.fixture
    def authenticated_user(self, api_client):
        user = User.objects.create_user(
            email='testuser@test.com',
            password='oldpass123'
        )
        api_client.force_authenticate(user=user)
        return api_client, user

    def test_successful_password_change(self, authenticated_user):
        """Ensures users can change password with correct credentials"""
        client, user = authenticated_user

        response = client.put('/api/password/', {
            'old_password': 'oldpass123',
            'new_password': 'newpass123'
        })
        assert response.status_code == status.HTTP_200_OK

        # Verify password was actually changed
        user.refresh_from_db()
        assert user.check_password('newpass123')

    def test_wrong_old_password(self, authenticated_user):
        """Ensures password change fails with incorrect old password"""
        client, _ = authenticated_user

        response = client.put('/api/password/', {
            'old_password': 'wrongpass',
            'new_password': 'newpass123'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data

    def test_unauthenticated_password_change(self, api_client):
        """Ensures unauthenticated users cannot change passwords"""

        client = api_client

        response = client.put('/api/password/', {
            'old_password': 'oldpass',
            'new_password': 'newpass'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED