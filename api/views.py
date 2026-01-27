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
import json

from .models import Installer, Installation, Document, AuditLog
from .serializers import (
    UserSerializer, LoginSerializer, RegisterSerializer,
    InstallerSerializer, InstallerNestedSerializer, InstallerCreateSerializer,
    InstallationSerializer, InstallationNestedSerializer,
    CreateInstallationSerializer, UpdateInstallationSerializer,
    InstallerRecommendationSerializer,
    DocumentSerializer, AuditLogSerializer,
    status_to_kebab_case, status_to_snake_case
)
from .services.geocoding import GeocodingService

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """Authentication views."""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login endpoint matching frontend format."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register new user (public registration)."""
        # Public registration: no admin check
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    
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
        """Get current user matching frontend format."""
        return Response({'user': UserSerializer(request.user).data})
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def refresh(self, request):
        """Refresh JWT token matching frontend format (accepts Bearer token in header)."""
        # Try to get refresh token from body first
        refresh_token = request.data.get('refresh')
        
        # If not in body, try to extract from Authorization header (Bearer token)
        if not refresh_token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                # Try to use the token as refresh token
                refresh_token = token
        
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
    """Installer views matching frontend format."""
    queryset = Installer.objects.select_related('user').all()
    serializer_class = InstallerNestedSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'bulk_import':
            return InstallerCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return InstallerUpdateSerializer
        return InstallerNestedSerializer
    
    def list(self, request, *args, **kwargs):
        """Return wrapped list response matching frontend format."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'installers': serializer.data})
    
    def retrieve(self, request, *args, **kwargs):
        """Return direct object matching frontend format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
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
        """Get installer recommendations based on location matching frontend format."""
        # Accept both lat/lng (frontend) and latitude/longitude (backend)
        latitude = request.query_params.get('latitude') or request.query_params.get('lat')
        longitude = request.query_params.get('longitude') or request.query_params.get('lng')
        radius_km = float(request.query_params.get('radius', 50))
        
        if not latitude or not longitude:
            return Response(
                {'error': 'latitude and longitude (or lat and lng) are required.'},
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
        recommendations = []
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
                # Calculate scores (simplified scoring)
                distance_score = max(0, 100 - (distance / radius_km * 100))
                availability_score = 100 if installer.availability == 'available' else 50
                workload_score = max(0, 100 - (installer.active_jobs_count * 10))
                total_score = (distance_score * 0.4 + availability_score * 0.3 + workload_score * 0.3)
                
                installer_data = InstallerNestedSerializer(installer).data
                recommendation = {
                    'installer': installer_data,
                    'distance': round(distance, 2),
                    'distanceScore': round(distance_score, 2),
                    'availabilityScore': round(availability_score, 2),
                    'workloadScore': round(workload_score, 2),
                    'totalScore': round(total_score, 2),
                    'explanation': f"Distance: {round(distance, 2)}km, Availability: {installer.availability}, Active jobs: {installer.active_jobs_count}"
                }
                recommendations.append(recommendation)
        
        # Sort by total score (descending)
        recommendations.sort(key=lambda x: x['totalScore'], reverse=True)
        
        return Response({'recommendations': recommendations})
    
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
    """Installation views matching frontend format."""
    queryset = Installation.objects.select_related(
        'assigned_installer', 'assigned_installer__user', 'created_by'
    ).all()
    serializer_class = InstallationNestedSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateInstallationSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UpdateInstallationSerializer
        return InstallationNestedSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Installers can only see their assigned installations
        if not self.request.user.is_admin:
            try:
                installer = self.request.user.installer_profile
                queryset = queryset.filter(assigned_installer=installer)
            except Installer.DoesNotExist:
                queryset = queryset.none()
        
        # Filter by status (accept both kebab-case and snake_case)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            # Try kebab-case first, then snake_case
            snake_case_status = status_to_snake_case(status_filter)
            queryset = queryset.filter(status=snake_case_status)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Return wrapped list response matching frontend format."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'installations': serializer.data})
    
    def retrieve(self, request, *args, **kwargs):
        """Return direct object matching frontend format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create installation from frontend format."""
        serializer = CreateInstallationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Extract installer_id if present
        installer_id = validated_data.pop('assigned_installer_id', None)
        
        installation = Installation.objects.create(
            created_by=request.user,
            **validated_data
        )
        
        if installer_id:
            try:
                installer = Installer.objects.get(id=installer_id)
                installation.assigned_installer = installer
                installation.assigned_at = timezone.now()
                installation.save()
            except Installer.DoesNotExist:
                pass
        
        return Response({
            'id': str(installation.id),
            'message': 'Installation created successfully'
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update installation from frontend format."""
        instance = self.get_object()
        serializer = UpdateInstallationSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Update fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        
        return Response({
            'id': str(instance.id),
            'message': 'Installation updated successfully'
        })
    
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        """Update installation status matching frontend format."""
        installation = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert kebab-case to snake_case
        snake_case_status = status_to_snake_case(new_status)
        
        if snake_case_status not in dict(Installation.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle rejected_by_installer status - set to pending_assignment and clear installer
        if snake_case_status == 'rejected_by_installer':
            # Track rejected installer in notes
            notes = installation.notes or []
            rejected_installers = []
            
            # Get existing rejected installers
            rejected_note = None
            for note in notes:
                if isinstance(note, str) and note.startswith('rejected_installers:'):
                    rejected_note = note
                    try:
                        rejected_installers = json.loads(note.replace('rejected_installers:', ''))
                        if not isinstance(rejected_installers, list):
                            rejected_installers = []
                    except:
                        rejected_installers = []
                    break
            
            # Add current installer if assigned and not already in list
            if installation.assigned_installer and str(installation.assigned_installer.id) not in rejected_installers:
                rejected_installers.append(str(installation.assigned_installer.id))
            
            # Update notes
            if rejected_note:
                notes = [note for note in notes if not (isinstance(note, str) and note.startswith('rejected_installers:'))]
            if rejected_installers:
                notes.append(f'rejected_installers:{json.dumps(rejected_installers)}')
            installation.notes = notes
            
            # Set status to pending_assignment and clear installer
            installation.status = 'pending_assignment'
            installation.assigned_installer = None
            installation.assigned_at = None
        else:
            installation.status = snake_case_status
        
        # Update timestamps based on status
        if snake_case_status == 'assigned' and not installation.assigned_at:
            installation.assigned_at = timezone.now()
        elif snake_case_status == 'accepted' and not installation.accepted_at:
            installation.accepted_at = timezone.now()
        elif snake_case_status == 'scheduled' and not installation.scheduled_at:
            installation.scheduled_at = timezone.now()
        elif snake_case_status == 'in_progress' and not installation.started_at:
            installation.started_at = timezone.now()
        elif snake_case_status == 'completed':
            installation.completed_at = timezone.now()
        elif snake_case_status == 'approved' and not installation.approved_at:
            installation.approved_at = timezone.now()
        
        installation.save()
        
        return Response({
            'id': str(installation.id),
            'status': status_to_kebab_case(installation.status),
            'message': 'Status updated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def assign_installer(self, request, pk=None):
        """Assign installer to installation matching frontend format."""
        installation = self.get_object()
        # Accept both installerId (frontend) and installer_id (backend)
        installer_id = request.data.get('installerId') or request.data.get('installer_id')
        
        if not installer_id:
            return Response(
                {'error': 'installerId is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            installer = Installer.objects.get(id=installer_id)
            installation.assigned_installer = installer
            installation.status = 'pending_acceptance'  # Set to pending_acceptance when assigning
            installation.assigned_at = timezone.now()
            installation.save()
            
            return Response({
                'id': str(installation.id),
                'message': 'Installer assigned successfully'
            })
        except Installer.DoesNotExist:
            return Response(
                {'error': 'Installer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        """Accept installation job (installer only)."""
        installation = self.get_object()
        
        # Check if user is an installer
        if request.user.is_admin:
            return Response(
                {'error': 'Only installers can accept jobs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            installer = request.user.installer_profile
        except Installer.DoesNotExist:
            return Response(
                {'error': 'Installer profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if installation is assigned to this installer
        if installation.assigned_installer != installer:
            return Response(
                {'error': 'This installation is not assigned to you.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if status is pending_acceptance
        if installation.status != 'pending_acceptance':
            return Response(
                {'error': 'Installation is not in pending acceptance status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to accepted
        installation.status = 'accepted'
        installation.accepted_at = timezone.now()
        installation.save()
        
        return Response({
            'id': str(installation.id),
            'status': status_to_kebab_case(installation.status),
            'message': 'Installation accepted successfully'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject installation job (installer only)."""
        installation = self.get_object()
        
        # Check if user is an installer
        if request.user.is_admin:
            return Response(
                {'error': 'Only installers can reject jobs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            installer = request.user.installer_profile
        except Installer.DoesNotExist:
            return Response(
                {'error': 'Installer profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if installation is assigned to this installer
        if installation.assigned_installer != installer:
            return Response(
                {'error': 'This installation is not assigned to you.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if status is pending_acceptance
        if installation.status != 'pending_acceptance':
            return Response(
                {'error': 'Installation is not in pending acceptance status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Track rejected installer in notes
        notes = installation.notes or []
        rejected_installers = []
        
        # Get existing rejected installers
        rejected_note = None
        for note in notes:
            if isinstance(note, str) and note.startswith('rejected_installers:'):
                rejected_note = note
                try:
                    rejected_installers = json.loads(note.replace('rejected_installers:', ''))
                    if not isinstance(rejected_installers, list):
                        rejected_installers = []
                except:
                    rejected_installers = []
                break
        
        # Add current installer if not already in list
        if str(installer.id) not in rejected_installers:
            rejected_installers.append(str(installer.id))
        
        # Update notes
        if rejected_note:
            notes = [note for note in notes if not (isinstance(note, str) and note.startswith('rejected_installers:'))]
        notes.append(f'rejected_installers:{json.dumps(rejected_installers)}')
        installation.notes = notes
        
        # Set status back to pending_assignment and clear installer
        installation.status = 'pending_assignment'
        installation.assigned_installer = None
        installation.assigned_at = None
        installation.save()
        
        return Response({
            'id': str(installation.id),
            'status': status_to_kebab_case(installation.status),
            'message': 'Installation rejected. Status set to pending assignment for reassignment.'
        })
    
    @action(detail=True, methods=['post', 'get'], url_path='documents')
    def documents(self, request, pk=None):
        """Handle document upload (POST) and list (GET) for installation matching frontend format."""
        installation = self.get_object()
        
        if request.method == 'POST':
            # Upload document
            file = request.FILES.get('file')
            category = request.data.get('category', 'photo')
            
            if not file:
                return Response(
                    {'error': 'file is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            document = Document.objects.create(
                installation=installation,
                document_type=category,
                category=category,
                file=file,
                description=request.data.get('description', '')
            )
            
            return Response({
                'id': str(document.id),
                'fileName': document.file_name,
                'filePath': document.file_path,
                'message': 'Document uploaded successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            # GET - List documents
            documents = installation.documents.all()
            serializer = DocumentSerializer(documents, many=True)
            return Response({'documents': serializer.data})


class DocumentViewSet(viewsets.ModelViewSet):
    """Document views matching frontend format."""
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
    
    def retrieve(self, request, *args, **kwargs):
        """Get document file for download."""
        instance = self.get_object()
        if instance.file:
            from django.http import FileResponse
            return FileResponse(instance.file.open(), as_attachment=True)
        return Response(
            {'error': 'File not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


class GeocodingViewSet(viewsets.ViewSet):
    """Geocoding views."""
    permission_classes = [AllowAny]  # Allow unauthenticated access for autocomplete
    
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
        """Reverse geocoding (coordinates to address) matching frontend format."""
        # Accept both lat/lng (frontend) and latitude/longitude (backend)
        latitude = request.data.get('latitude') or request.data.get('lat')
        longitude = request.data.get('longitude') or request.data.get('lng')
        
        if not latitude or not longitude:
            return Response(
                {'error': 'latitude and longitude (or lat and lng) are required.'},
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
        """Address autocomplete matching frontend format."""
        query = request.data.get('query')
        limit = int(request.data.get('limit', 5))
        
        if not query:
            return Response(
                {'error': 'query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            results = self.geocoding_service.autocomplete(query)
            # Limit results
            if limit and len(results) > limit:
                results = results[:limit]
            # Return empty array if no API key configured (instead of error)
            return Response({'results': results or []})
        except Exception as e:
            # Return empty results instead of error if API key is missing
            return Response({'results': []})
    
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
