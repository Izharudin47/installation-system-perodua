"""
API URL routing matching frontend expectations.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, InstallerViewSet, InstallationViewSet,
    DocumentViewSet, GeocodingViewSet
)

# Configure router to handle trailing slashes properly
router = DefaultRouter(trailing_slash=False)
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'installers', InstallerViewSet, basename='installer')
router.register(r'installations', InstallationViewSet, basename='installation')
router.register(r'geocoding', GeocodingViewSet, basename='geocoding')
# Register documents as 'files' to match frontend API calls
router.register(r'files', DocumentViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
]
