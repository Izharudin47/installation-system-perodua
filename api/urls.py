"""
API URL routing.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, InstallerViewSet, InstallationViewSet,
    DocumentViewSet, GeocodingViewSet
)
``
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'installers', InstallerViewSet, basename='installer')
router.register(r'installations', InstallationViewSet, basename='installation')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'geocoding', GeocodingViewSet, basename='geocoding')

urlpatterns = [
    path('', include(router.urls)),
]
