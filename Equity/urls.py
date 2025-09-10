from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler400, handler403, handler404, handler500
from banking_system import views as banking_views  # import your app views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('banking_system.urls')),  # include your app urls
]

# Serve static & media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler400 = 'banking_system.views.custom_400'
handler403 = 'banking_system.views.custom_403'
handler404 = 'banking_system.views.custom_404'
handler500 = 'banking_system.views.custom_500'
