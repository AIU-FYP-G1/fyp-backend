from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Profile


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'password', 'full_name')
        extra_kwargs = {
            'password': {'write_only': True},
            'full_name': {'required': True}
        }

    def validate_full_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Full name cannot be empty.")
        return value.strip()

    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        password = validated_data.pop('password')

        user = get_user_model().objects.create(
            email=validated_data['email']
        )
        user.set_password(password)
        user.save()

        Profile.objects.create(
            user=user,
            full_name=full_name
        )

        return user


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = "__all__"


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        return value
