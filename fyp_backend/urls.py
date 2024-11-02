from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from fyp_backend import settings

router = DefaultRouter()

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', include(router.urls)),
                  path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
