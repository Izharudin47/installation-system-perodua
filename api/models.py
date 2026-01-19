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
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    @property
    def is_admin(self):
        return self.role == 'admin'


class Installer(models.Model):
    """Installer profile information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='installer_profile')
    company = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['company']
    
    def __str__(self):
        return f"{self.company} - {self.name}"


class Installation(models.Model):
    """Installation job/request."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    charger_type = models.CharField(max_length=255, blank=True)
    installation_notes = models.TextField(blank=True)
    
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
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
