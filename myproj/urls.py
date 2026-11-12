from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include(('onlinestore.urls', 'onlinestore'), namespace='main')),
    path('base/', include(('onlinestore.urls', 'onlinestore'), namespace='base')),    #path('accounts/', include('django.contrib.auth.urls'))
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
