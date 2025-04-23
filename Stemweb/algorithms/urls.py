from django.urls import re_path
from .views import base, details, delete_runs, run, results, available, process
from .views import jobstatus, processtest, testresponse, testserver

from .settings import ALGORITHM_URL_PREFIX as prefix

urlpatterns = [
    re_path(r'^%s/base/' % prefix, base, name = 'algorithms_base_url'),
    re_path(r'^%s/(?P<algo_id>\d+)/$' % prefix, details, name = 'algorithms_details_url'),
    re_path(r'^%s/delete/$' % prefix, delete_runs, name = 'algorithms_delete_runs_url'),
    re_path(r'^%s/run/(?P<algo_id>\d+)/$' % prefix, run, name = 'algorithms_run_algorithm_url'),
    re_path(r'^%s/results/(?P<run_id>\d+)/$' % prefix, results, name = 'algorithms_run_results_url'),

    # Following urls are for external algorithm runs.
    re_path(r'^%s/available/$' % prefix, available, name = 'algorithms_available_url'),
    re_path(r'^%s/process/(?P<algo_id>\d+)/$' % prefix, process, name = 'algorithms_process_url'),
    re_path(r'^%s/jobstatus/(?P<run_id>\d+)/$' % prefix, jobstatus, name = 'algorithms_jobstatus_url'),

    # Test URL
    re_path(r'^%s/processtest/$' % prefix, processtest, name = 'algorithms_test_url'),
    re_path(r'^%s/testresponse/$' % prefix, testresponse, name = 'algorithms_testresponse_url'),
    re_path(r'^%s/testserver/$' % prefix, testserver, name = 'algorithms_testserver_url'),
]
