"""
URL configuration for watson project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,re_path
from django.urls.conf import include
from django.conf import settings
from django.conf.urls.static import static
from front import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title='WATSON API',
        default_version='v1',
        description='API 설명란',
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="a@a.com"),     # 부가 정보
        license=openapi.License(name="test")
    ),
    public=True,
    permission_classes=[permissions.AllowAny]
)


urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("view/", include("front.urls")),
    path("api/account/", include("accounts.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/chatbot/", include("chatbot.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name="schema-json"),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]



