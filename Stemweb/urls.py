from . import settings
from django.urls import include, re_path
from django.views import static
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    re_path(r'^', include('Stemweb.home.urls')),
    re_path(r'^files/', include('Stemweb.files.urls')),
    re_path(r'^', include('Stemweb.algorithms.urls')),
    re_path(r'^media/(?P<path>.*)$', static.serve,
        {'document_root': settings.MEDIA_ROOT},
        name='stemweb_media_root_url'),

    # These are the registration apps own urls. Check documentation for the usage.
    # https://bitbucket.org/ubernostrum/django-registration/src/tip/docs/quickstart.rst
    #(r'^accounts/', include('registration.backends.default.urls')),
    #re_path(r'^accounts/', include('Stemweb.third_party_apps.registration.backends.default.urls')),
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', admin.site.urls),
]
