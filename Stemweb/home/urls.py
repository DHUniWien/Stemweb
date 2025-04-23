from django.urls import re_path
from .views import home, server_error, script_failure

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    re_path(r'^home', home, name='stemweb_home_url'),
    re_path(r'^server_error', server_error, name='stemweb_server_error_url'),
    re_path(r'^script_failure', script_failure, name='stemweb_script_failure_url' ),
    re_path(r'^$', home),
]
