"""
Django REST Framework serializers.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Installer, Installation, Document, AuditLog


def status_to_kebab_case(status):
    """Convert snake_case status to kebab-case for frontend."""
    return status.replace('_', '-') if status else status


def status_to_snake_case(status):
    """Convert kebab-case status to snake_case for backend."""
    return status.replace('-', '_') if status else status


class UserSerializer(serializers.ModelSerializer):
    """User serializer matching frontend format."""
    name = serializers.SerializerMethodField()
    installerId = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'avatar', 'installerId']
        read_only_fields = ['id']
    
    def get_name(self, obj):
        """Combine first_name and last_name."""
        return obj.name
    
    def get_installerId(self, obj):
        """Get installer ID if user is an installer."""
        try:
            return str(obj.installer_profile.id)
        except Installer.DoesNotExist:
            return None


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


class InstallerNestedSerializer(serializers.ModelSerializer):
    """Installer serializer matching frontend nested structure."""
    email = serializers.EmailField(source='user.email', read_only=True)
    completedJobs = serializers.IntegerField(source='completed_jobs_count', read_only=True)
    activeJobs = serializers.IntegerField(source='active_jobs_count', read_only=True)
    pendingJobs = serializers.IntegerField(source='pending_jobs_count', read_only=True)
    availability = serializers.CharField(read_only=True)
    location = serializers.SerializerMethodField()
    joinedDate = serializers.DateTimeField(source='created_at', read_only=True)
    lastActive = serializers.DateTimeField(source='last_active', read_only=True, allow_null=True)
    compliance = serializers.SerializerMethodField()
    
    class Meta:
        model = Installer
        fields = [
            'id', 'name', 'company', 'phone', 'email',
            'completedJobs', 'activeJobs', 'pendingJobs',
            'specialties', 'availability', 'location',
            'certifications', 'joinedDate', 'lastActive', 'compliance'
        ]
        read_only_fields = ['id']
    
    def get_location(self, obj):
        """Transform location fields to nested structure."""
        return {
            'city': obj.city or '',
            'state': obj.state or '',
            'coverage': obj.coverage or [],
            'coordinates': {
                'lat': float(obj.latitude) if obj.latitude else None,
                'lng': float(obj.longitude) if obj.longitude else None
            } if obj.latitude and obj.longitude else None
        }
    
    def get_compliance(self, obj):
        """Return compliance data."""
        return obj.compliance_data or {}


class InstallerSerializer(serializers.ModelSerializer):
    """Installer serializer (legacy, for internal use)."""
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


class InstallationNestedSerializer(serializers.ModelSerializer):
    """Installation serializer matching frontend nested structure."""
    id = serializers.SerializerMethodField()  # Convert to string
    status = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    charger = serializers.SerializerMethodField()
    installer = serializers.SerializerMethodField()
    survey = serializers.SerializerMethodField()
    scheduling = serializers.SerializerMethodField()
    installation = serializers.SerializerMethodField()
    documentation = serializers.SerializerMethodField()
    timestamps = serializers.SerializerMethodField()
    adminReview = serializers.SerializerMethodField()
    priority = serializers.CharField(read_only=True)
    notes = serializers.JSONField(read_only=True)
    
    class Meta:
        model = Installation
        fields = [
            'id', 'status', 'customer', 'charger', 'installer',
            'survey', 'scheduling', 'installation', 'documentation',
            'timestamps', 'adminReview', 'priority', 'notes'
        ]
        read_only_fields = ['id']
    
    def get_id(self, obj):
        """Convert ID to string for frontend compatibility."""
        return str(obj.id)
    
    def get_status(self, obj):
        """Transform status to kebab-case."""
        return status_to_kebab_case(obj.status)
    
    def get_customer(self, obj):
        """Transform customer fields to nested structure."""
        return {
            'name': obj.customer_name,
            'email': obj.customer_email,
            'phone': obj.customer_phone,
            'address': {
                'street': obj.customer_street or obj.address or '',
                'city': obj.customer_city or '',
                'state': obj.customer_state or '',
                'postalCode': obj.customer_postal_code or obj.postal_code or '',
                'coordinates': {
                    'lat': float(obj.latitude) if obj.latitude else None,
                    'lng': float(obj.longitude) if obj.longitude else None
                } if obj.latitude and obj.longitude else None
            },
            'propertyType': obj.property_type or 'residential'
        }
    
    def get_charger(self, obj):
        """Transform charger fields to nested structure."""
        return {
            'model': obj.charger_model or obj.charger_type or '',
            'powerOutput': obj.charger_power_output or '',
            'installationType': obj.charger_installation_type or '',
            'manufacturer': obj.charger_manufacturer or ''
        }
    
    def get_installer(self, obj):
        """Transform assigned installer to nested structure."""
        if not obj.assigned_installer:
            return None
        
        installer = obj.assigned_installer
        return {
            'id': str(installer.id),
            'name': installer.name,
            'company': installer.company,
            'phone': installer.phone,
            'email': installer.user.email,
            'completedJobs': installer.completed_jobs_count
        }
    
    def get_survey(self, obj):
        """Return survey data."""
        return obj.survey_data if obj.survey_data else None
    
    def get_scheduling(self, obj):
        """Return scheduling data."""
        return obj.scheduling_data if obj.scheduling_data else None
    
    def get_installation(self, obj):
        """Return installation progress data."""
        return obj.installation_data if obj.installation_data else None
    
    def get_documentation(self, obj):
        """Return documentation data."""
        return obj.documentation_data if obj.documentation_data else None
    
    def get_timestamps(self, obj):
        """Transform timestamp fields to nested structure."""
        from django.utils.dateparse import parse_datetime
        return {
            'created': obj.created_at.isoformat() if obj.created_at else '',
            'assigned': obj.assigned_at.isoformat() if obj.assigned_at else None,
            'accepted': obj.accepted_at.isoformat() if obj.accepted_at else None,
            'scheduled': obj.scheduled_at.isoformat() if obj.scheduled_at else None,
            'started': obj.started_at.isoformat() if obj.started_at else None,
            'completed': obj.completed_at.isoformat() if obj.completed_at else None,
            'approved': obj.approved_at.isoformat() if obj.approved_at else None
        }
    
    def get_adminReview(self, obj):
        """Return admin review data."""
        return obj.admin_review_data if obj.admin_review_data else None


class InstallationSerializer(serializers.ModelSerializer):
    """Installation serializer (legacy, for internal use)."""
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


class CreateInstallationSerializer(serializers.Serializer):
    """Serializer for creating installations from frontend format."""
    # Accept both nested and flat formats
    customer = serializers.DictField(required=False)
    charger = serializers.DictField(required=False)
    # Flat format fields (from frontend)
    customerName = serializers.CharField(required=False)
    customerEmail = serializers.EmailField(required=False)
    customerPhone = serializers.CharField(required=False)
    customerStreet = serializers.CharField(required=False)
    customerCity = serializers.CharField(required=False)
    customerState = serializers.CharField(required=False)
    customerPostalCode = serializers.CharField(required=False)
    propertyType = serializers.ChoiceField(choices=['residential', 'commercial'], required=False, default='residential')
    chargerModel = serializers.CharField(required=False)
    chargerPowerOutput = serializers.CharField(required=False)
    installationType = serializers.CharField(required=False)
    manufacturer = serializers.CharField(required=False)
    installerId = serializers.CharField(required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high', 'urgent'], default='medium')
    status = serializers.CharField(required=False)
    
    def validate(self, attrs):
        """Validate and transform frontend format to backend format."""
        # Check if nested format (customer/charger dicts) or flat format
        if attrs.get('customer') and attrs.get('charger'):
            # Nested format
            customer = attrs.get('customer', {})
            charger = attrs.get('charger', {})
            address = customer.get('address', {})
            
            validated_data = {
                'customer_name': customer.get('name', ''),
                'customer_email': customer.get('email', ''),
                'customer_phone': customer.get('phone', ''),
                'customer_street': address.get('street', ''),
                'customer_city': address.get('city', ''),
                'customer_state': address.get('state', ''),
                'customer_postal_code': address.get('postalCode', ''),
                'property_type': customer.get('propertyType', 'residential'),
                'charger_model': charger.get('model', ''),
                'charger_power_output': charger.get('powerOutput', ''),
                'charger_installation_type': charger.get('installationType', ''),
                'charger_manufacturer': charger.get('manufacturer', ''),
                'priority': attrs.get('priority', 'medium'),
                'latitude': address.get('coordinates', {}).get('lat'),
                'longitude': address.get('coordinates', {}).get('lng'),
                'postal_code': address.get('postalCode', ''),
                'address': address.get('street', ''),
            }
        else:
            # Flat format (from frontend)
            validated_data = {
                'customer_name': attrs.get('customerName', ''),
                'customer_email': attrs.get('customerEmail', ''),
                'customer_phone': attrs.get('customerPhone', ''),
                'customer_street': attrs.get('customerStreet', ''),
                'customer_city': attrs.get('customerCity', ''),
                'customer_state': attrs.get('customerState', ''),
                'customer_postal_code': attrs.get('customerPostalCode', ''),
                'property_type': attrs.get('propertyType', 'residential'),
                'charger_model': attrs.get('chargerModel', ''),
                'charger_power_output': attrs.get('chargerPowerOutput', ''),
                'charger_installation_type': attrs.get('installationType', ''),
                'charger_manufacturer': attrs.get('manufacturer', ''),
                'priority': attrs.get('priority', 'medium'),
                'postal_code': attrs.get('customerPostalCode', ''),
                'address': attrs.get('customerStreet', ''),
            }
        
        # Handle installer ID and set status accordingly
        installer_id = attrs.get('installerId')
        if installer_id:
            validated_data['assigned_installer_id'] = int(installer_id)
            # If installer is assigned, status should be 'pending_acceptance'
            # Otherwise, use provided status or default to 'pending_assignment'
            if not attrs.get('status'):
                validated_data['status'] = 'pending_acceptance'
            else:
                validated_data['status'] = status_to_snake_case(attrs.get('status'))
        else:
            # No installer assigned, use provided status or default to 'pending_assignment'
            validated_data['status'] = status_to_snake_case(attrs.get('status', 'pending_assignment'))
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_email', 'customer_phone', 'customer_street', 'customer_city', 'customer_state']
        missing_fields = [field for field in required_fields if not validated_data.get(field)]
        if missing_fields:
            raise serializers.ValidationError(f'Missing required fields: {", ".join(missing_fields)}')
        
        return validated_data


class UpdateInstallationSerializer(serializers.Serializer):
    """Serializer for updating installations from frontend format."""
    customer = serializers.DictField(required=False)
    charger = serializers.DictField(required=False)
    status = serializers.CharField(required=False)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high', 'urgent'], required=False)
    notes = serializers.ListField(child=serializers.CharField(), required=False)
    
    def validate(self, attrs):
        """Validate and transform frontend format to backend format."""
        validated_data = {}
        
        if 'customer' in attrs:
            customer = attrs['customer']
            address = customer.get('address', {})
            validated_data.update({
                'customer_name': customer.get('name'),
                'customer_email': customer.get('email'),
                'customer_phone': customer.get('phone'),
                'customer_street': address.get('street'),
                'customer_city': address.get('city'),
                'customer_state': address.get('state'),
                'customer_postal_code': address.get('postalCode'),
                'property_type': customer.get('propertyType'),
                'latitude': address.get('coordinates', {}).get('lat'),
                'longitude': address.get('coordinates', {}).get('lng'),
                'postal_code': address.get('postalCode'),
                'address': address.get('street'),
            })
        
        if 'charger' in attrs:
            charger = attrs['charger']
            validated_data.update({
                'charger_model': charger.get('model'),
                'charger_power_output': charger.get('powerOutput'),
                'charger_installation_type': charger.get('installationType'),
                'charger_manufacturer': charger.get('manufacturer'),
            })
        
        if 'status' in attrs:
            validated_data['status'] = status_to_snake_case(attrs['status'])
        
        if 'priority' in attrs:
            validated_data['priority'] = attrs['priority']
        
        if 'notes' in attrs:
            validated_data['notes'] = attrs['notes']
        
        return validated_data


class InstallerRecommendationSerializer(serializers.Serializer):
    """Serializer for installer recommendations matching frontend format."""
    installer = InstallerNestedSerializer()
    distance = serializers.FloatField()
    distanceScore = serializers.FloatField()
    availabilityScore = serializers.FloatField()
    workloadScore = serializers.FloatField()
    totalScore = serializers.FloatField()
    explanation = serializers.CharField()


class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer matching frontend format."""
    id = serializers.CharField(source='id', read_only=True)
    fileName = serializers.SerializerMethodField()
    filePath = serializers.SerializerMethodField()
    fileType = serializers.SerializerMethodField()
    fileSize = serializers.IntegerField(source='file_size', read_only=True)
    category = serializers.CharField(source='category', read_only=True)
    uploadedAt = serializers.DateTimeField(source='uploaded_at', read_only=True)
    
    class Meta:
        model = Document
        fields = ['id', 'fileName', 'filePath', 'fileType', 'fileSize', 'category', 'uploadedAt']
        read_only_fields = ['id', 'uploadedAt']
    
    def get_fileName(self, obj):
        """Get file name."""
        return obj.file_name
    
    def get_filePath(self, obj):
        """Get file path."""
        return obj.file_path
    
    def get_fileType(self, obj):
        """Get file type from file extension."""
        if obj.file:
            return obj.file.name.split('.')[-1].lower() if '.' in obj.file.name else ''
        return ''


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'model_name', 'object_id', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']
