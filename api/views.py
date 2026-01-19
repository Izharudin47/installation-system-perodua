"""
Django REST Framework views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
import math

from .models import Installer, Installation, Document, AuditLog
from .serializers import (
    UserSerializer, LoginSerializer, RegisterSerializer,
    InstallerSerializer, InstallerCreateSerializer,
    InstallationSerializer, DocumentSerializer, AuditLogSerializer
)
from .services.geocoding import GeocodingService

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """Authentication views."""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login endpoint."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def register(self, request):
        """Register new user (admin only)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can create new users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def register_admin(self, request):
        """Register new admin (admin only)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can create admin users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data.copy()
        data['role'] = 'admin'
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user."""
        return Response(UserSerializer(request.user).data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def refresh(self, request):
        """Refresh JWT token."""
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'token': str(refresh.access_token),
            })
        except Exception as e:
            return Response(
                {'error': 'Invalid refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class InstallerViewSet(viewsets.ModelViewSet):
    """Installer views."""
    queryset = Installer.objects.select_related('user').all()
    serializer_class = InstallerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'bulk_import':
            return InstallerCreateSerializer
        return InstallerSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Installers can only see themselves
        if not self.request.user.is_admin:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by coverage area
        coverage = self.request.query_params.get('coverage')
        if coverage:
            queryset = queryset.filter(coverage__contains=[coverage])
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get installer recommendations based on location."""
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius_km = float(request.query_params.get('radius', 50))
        
        if not latitude or not longitude:
            return Response(
                {'error': 'latitude and longitude are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(latitude)
            lng = float(longitude)
        except ValueError:
            return Response(
                {'error': 'Invalid latitude or longitude.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find installers within radius
        installers = []
        for installer in Installer.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ):
            distance = self._calculate_distance(
                lat, lng,
                float(installer.latitude),
                float(installer.longitude)
            )
            if distance <= radius_km:
                installer_data = InstallerSerializer(installer).data
                installer_data['distance_km'] = round(distance, 2)
                installers.append(installer_data)
        
        # Sort by distance
        installers.sort(key=lambda x: x['distance_km'])
        
        return Response(installers)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_import(self, request):
        """Bulk import installers."""
        installers_data = request.data.get('installers', [])
        if not installers_data:
            return Response(
                {'error': 'installers array is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created = []
        errors = []
        
        for idx, installer_data in enumerate(installers_data):
            try:
                # Set default password if not provided
                if 'password' not in installer_data:
                    installer_data['password'] = 'Installer123!'
                
                serializer = InstallerCreateSerializer(data=installer_data)
                if serializer.is_valid():
                    installer = serializer.save()
                    created.append(InstallerSerializer(installer).data)
                else:
                    errors.append({
                        'index': idx,
                        'data': installer_data,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'index': idx,
                    'data': installer_data,
                    'error': str(e)
                })
        
        return Response({
            'created': len(created),
            'errors': len(errors),
            'installers': created,
            'error_details': errors
        }, status=status.HTTP_201_CREATED)
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in kilometers (Haversine formula)."""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


class InstallationViewSet(viewsets.ModelViewSet):
    """Installation views."""
    queryset = Installation.objects.select_related(
        'assigned_installer', 'assigned_installer__user', 'created_by'
    ).all()
    serializer_class = InstallationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Installers can only see their assigned installations
        if not self.request.user.is_admin:
            try:
                installer = self.request.user.installer_profile
                queryset = queryset.filter(assigned_installer=installer)
            except Installer.DoesNotExist:
                queryset = queryset.none()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        """Update installation status."""
        installation = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Installation.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        installation.status = new_status
        if new_status == 'completed':
            installation.completed_at = timezone.now()
        installation.save()
        
        return Response(InstallationSerializer(installation).data)
    
    @action(detail=True, methods=['post'])
    def assign_installer(self, request, pk=None):
        """Assign installer to installation."""
        installation = self.get_object()
        installer_id = request.data.get('installer_id')
        
        if not installer_id:
            return Response(
                {'error': 'installer_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            installer = Installer.objects.get(id=installer_id)
            installation.assigned_installer = installer
            installation.status = 'assigned'
            installation.save()
            
            return Response(InstallationSerializer(installation).data)
        except Installer.DoesNotExist:
            return Response(
                {'error': 'Installer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class DocumentViewSet(viewsets.ModelViewSet):
    """Document views."""
    queryset = Document.objects.select_related('installation').all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by installation if provided
        installation_id = self.request.query_params.get('installation_id')
        if installation_id:
            queryset = queryset.filter(installation_id=installation_id)
        
        # Installers can only see documents for their installations
        if not self.request.user.is_admin:
            try:
                installer = self.request.user.installer_profile
                queryset = queryset.filter(
                    installation__assigned_installer=installer
                )
            except Installer.DoesNotExist:
                queryset = queryset.none()
        
        return queryset


class GeocodingViewSet(viewsets.ViewSet):
    """Geocoding views."""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geocoding_service = GeocodingService()
    
    @action(detail=False, methods=['post'])
    def forward(self, request):
        """Forward geocoding (address to coordinates)."""
        address = request.data.get('address')
        if not address:
            return Response(
                {'error': 'address is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = self.geocoding_service.forward_geocode(address)
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def reverse(self, request):
        """Reverse geocoding (coordinates to address)."""
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if not latitude or not longitude:
            return Response(
                {'error': 'latitude and longitude are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = self.geocoding_service.reverse_geocode(
                float(latitude),
                float(longitude)
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def autocomplete(self, request):
        """Address autocomplete."""
        query = request.data.get('query')
        if not query:
            return Response(
                {'error': 'query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            results = self.geocoding_service.autocomplete(query)
            return Response(results)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def radius(self, request):
        """Radius search."""
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        radius_km = float(request.data.get('radius', 50))
        
        if not latitude or not longitude:
            return Response(
                {'error': 'latitude and longitude are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            results = self.geocoding_service.radius_search(
                float(latitude),
                float(longitude),
                radius_km
            )
            return Response(results)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
