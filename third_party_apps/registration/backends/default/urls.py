"""
URLconf for registration and activation, using django-registration's
one-step backend.

If the default behavior of these views is acceptable to you, simply
use a line like this in your root URLconf to set up the default URLs
for registration::

    (r'^accounts/', include('registration.backends.simple.urls')),

This will also automatically set up the views in
``django.contrib.auth`` at sensible default locations.

If you'd like to customize the behavior (e.g., by passing extra
arguments to the various views) or split up the URLs, feel free to set
up your own URL patterns for these views instead.

"""


from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from Stemweb.third_party_apps.registration.views import activate
from Stemweb.third_party_apps.registration.views import register


urlpatterns = patterns('',
                       url(r'^register/$',
                           register,
                           {'backend': 'Stemweb.third_party_apps.registration.backends.default.DefaultBackend'},
                           name='registration_register'),
                       url(r'^register/closed/$',
                           direct_to_template,
                           {'template': 'registration/registration_closed.html'},
                           name='registration_disallowed'),
                       (r'', include('Stemweb.third_party_apps.registration.auth_urls')),
                       )