"""
Django REST Framework serializers.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Installer, Installation, Document, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'first_name', 'last_name']
        read_only_fields = ['id']


class LoginSerializer(serializers.Serializer):
    """Login serializer."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include "email" and "password".')
        
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """Registration serializer."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'role', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class InstallerSerializer(serializers.ModelSerializer):
    """Installer serializer."""
    user = UserSerializer(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Installer
        fields = [
            'id', 'user', 'email', 'company', 'name', 'phone', 'address',
            'latitude', 'longitude', 'coverage', 'specialties', 'certifications',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InstallerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating installers."""
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    class Meta:
        model = Installer
        fields = [
            'email', 'password', 'company', 'name', 'phone', 'address',
            'latitude', 'longitude', 'coverage', 'specialties', 'certifications'
        ]
    
    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            role='installer'
        )
        
        installer = Installer.objects.create(user=user, **validated_data)
        return installer


class InstallationSerializer(serializers.ModelSerializer):
    """Installation serializer."""
    assigned_installer = InstallerSerializer(read_only=True)
    assigned_installer_id = serializers.IntegerField(write_only=True, required=False)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Installation
        fields = [
            'id', 'status', 'customer_name', 'customer_email', 'customer_phone',
            'address', 'latitude', 'longitude', 'postal_code', 'charger_type',
            'installation_notes', 'assigned_installer', 'assigned_installer_id',
            'created_by', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer."""
    class Meta:
        model = Document
        fields = ['id', 'installation', 'document_type', 'file', 'description', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'model_name', 'object_id', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']
