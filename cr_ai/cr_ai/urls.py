"""cr_ai URL Configuratio
"""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ai_pred.urls')),
]
