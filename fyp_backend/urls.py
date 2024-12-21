from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import SignUpView, CustomTokenObtainPairView, ProfileUpdateView, ChangePasswordView
from fyp_backend import settings
from patients.views import PatientListCreateView, PatientDetailView, DiagnosisListCreateView, DiagnosisDetailView

router = DefaultRouter()

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', include(router.urls)),
                  path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('signup/', SignUpView.as_view(), name='signup'),
                  path('login/', CustomTokenObtainPairView.as_view(), name='login'),
                  path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('profile/', ProfileUpdateView.as_view(), name='profile-update'),
                  path('password/', ChangePasswordView.as_view(), name='change-password'),

                  path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
                  path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),

                  path('patients/<int:patient_id>/diagnoses/', DiagnosisListCreateView.as_view(),
                       name='diagnosis-list-create'),
                  path('patients/<int:patient_id>/diagnoses/<int:pk>/', DiagnosisDetailView.as_view(),
                       name='diagnosis-detail'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL,
                                                                                         document_root=settings.STATIC_ROOT)
