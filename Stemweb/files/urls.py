from django.urls import re_path
from .views import details, base, upload

urlpatterns = [
    re_path(r'^(?P<file_id>\d+)/$', details, name='files_details_url'),
    re_path(r'^base', base, name='files_base_url'),
    re_path(r'^upload', upload, name='files_upload_url')
]
