from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, ROLE_CHOICES


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )


class UserSerializer(serializers.ModelSerializer):
    role_label   = serializers.ReadOnlyField()
    is_staff_role = serializers.ReadOnlyField()
    is_admin_role = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'role',
            'role_label', 'is_staff_role', 'is_admin_role',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class UserBriefSerializer(serializers.ModelSerializer):
    """Compact serializer used in nested contexts (logs, analytics)."""
    role_label = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'role', 'role_label']
