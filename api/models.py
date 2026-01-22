"""
Django models for Installation System.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator


class User(AbstractUser):
    """Custom User model with role support."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('installer', 'Installer'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='installer')
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    avatar = models.URLField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def name(self):
        """Combine first_name and last_name for frontend compatibility."""
        parts = [self.first_name, self.last_name]
        return ' '.join(filter(None, parts)) or self.email.split('@')[0]


class Installer(models.Model):
    """Installer profile information."""
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('unavailable', 'Unavailable'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='installer_profile')
    company = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Coverage areas
    COVERAGE_CHOICES = [
        ('C1', 'Central 1'),
        ('C2', 'Central 2'),
        ('Northen', 'Northern'),
        ('Southern', 'Southern'),
        ('East Coast', 'East Coast'),
        ("East M'sia", "East Malaysia"),
    ]
    coverage = models.JSONField(default=list)  # List of coverage areas
    
    specialties = models.JSONField(default=list)  # List of specialties
    certifications = models.JSONField(default=list)  # List of certifications
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    compliance_data = models.JSONField(default=dict)  # Compliance information (ST, CIDB, SST, etc.)
    last_active = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['company']
    
    def __str__(self):
        return f"{self.company} - {self.name}"
    
    @property
    def completed_jobs_count(self):
        """Count of completed installations."""
        return self.installations.filter(status='completed').count()
    
    @property
    def active_jobs_count(self):
        """Count of active installations."""
        active_statuses = ['in_progress', 'survey_in_progress', 'scheduled', 'testing']
        return self.installations.filter(status__in=active_statuses).count()
    
    @property
    def pending_jobs_count(self):
        """Count of pending installations."""
        pending_statuses = ['pending_assignment', 'pending_acceptance', 'assigned', 'accepted']
        return self.installations.filter(status__in=pending_statuses).count()


class Installation(models.Model):
    """Installation job/request."""
    STATUS_CHOICES = [
        ('pending_assignment', 'Pending Assignment'),
        ('pending_acceptance', 'Pending Acceptance'),
        ('declined', 'Declined'),
        ('rejected_by_installer', 'Rejected by Installer'),
        ('accepted', 'Accepted'),
        ('survey_in_progress', 'Survey In Progress'),
        ('pending_customer_approval', 'Pending Customer Approval'),
        ('approved_for_installation', 'Approved for Installation'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('testing', 'Testing'),
        ('completed', 'Completed'),
        ('under_admin_review', 'Under Admin Review'),
        ('approved', 'Approved'),
        ('failed', 'Failed'),
        ('on_hold', 'On Hold'),
        # Legacy statuses for backward compatibility
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
    ]
    
    INSTALLATION_TYPE_CHOICES = [
        ('wall-mounted', 'Wall Mounted'),
        ('pedestal', 'Pedestal'),
        ('floor-mounted', 'Floor Mounted'),
    ]
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_assignment')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Customer information
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_street = models.CharField(max_length=255, blank=True)
    customer_city = models.CharField(max_length=100, blank=True)
    customer_state = models.CharField(max_length=100, blank=True)
    customer_postal_code = models.CharField(max_length=10, blank=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='residential')
    
    # Address (legacy field, kept for backward compatibility)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)  # Legacy field
    
    # Charger information
    charger_model = models.CharField(max_length=255, blank=True)
    charger_power_output = models.CharField(max_length=50, blank=True)
    charger_installation_type = models.CharField(max_length=20, choices=INSTALLATION_TYPE_CHOICES, blank=True)
    charger_manufacturer = models.CharField(max_length=255, blank=True)
    charger_type = models.CharField(max_length=255, blank=True)  # Legacy field
    
    # Additional data stored as JSON
    survey_data = models.JSONField(default=dict, blank=True)
    scheduling_data = models.JSONField(default=dict, blank=True)
    installation_data = models.JSONField(default=dict, blank=True)
    documentation_data = models.JSONField(default=dict, blank=True)
    admin_review_data = models.JSONField(default=dict, blank=True)
    notes = models.JSONField(default=list, blank=True)  # Array of note strings
    
    installation_notes = models.TextField(blank=True)  # Legacy field
    
    assigned_installer = models.ForeignKey(
        Installer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installations'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_installations'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Installation #{self.id} - {self.customer_name}"


class Document(models.Model):
    """File/document associated with installations."""
    DOCUMENT_TYPES = [
        ('photo', 'Photo'),
        ('certificate', 'Certificate'),
        ('invoice', 'Invoice'),
        ('document', 'Document'),
        ('survey', 'Survey'),
        ('completion', 'Completion'),
        ('other', 'Other'),
    ]
    
    installation = models.ForeignKey(
        Installation,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='photo')
    file = models.FileField(upload_to='documents/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.document_type} - {self.installation.id}"
    
    @property
    def category(self):
        """Alias for document_type to match frontend format."""
        return self.document_type
    
    @category.setter
    def category(self, value):
        """Set document_type when category is set."""
        self.document_type = value
    
    @property
    def file_name(self):
        """Get file name from file path."""
        if self.file:
            return self.file.name.split('/')[-1]
        return ''
    
    @property
    def file_path(self):
        """Get file path."""
        if self.file:
            return self.file.url
        return ''
    
    @property
    def file_size(self):
        """Get file size in bytes."""
        try:
            if self.file:
                return self.file.size
        except:
            pass
        return 0


class AuditLog(models.Model):
    """Activity tracking/audit log."""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('assign', 'Assign'),
        ('status_change', 'Status Change'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.IntegerField()
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.model_name} #{self.object_id}"
