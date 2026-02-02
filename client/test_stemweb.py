import time
import logging
import pytest
from stemweb_pytest_client import app

#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s-%(message)s')
#logging.basicConfig(level=logging.DEBUG, filename='/src/app/testingClient.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')

"""
Basic functional & integration tests for stemweb, using 3 different algorithms.
Send requests to the stemweb service using the respective test data in `client/requests`.
Stemweb returns responses in json format.
"""


def wait_for_job_finished(app, jobid, timeout, poll_interval=1):
    start = time.time()
    while time.time() - start < timeout:
        jobstatus = app.query_job(jobid)
        if jobstatus["status"] == 0:
            return jobstatus
        time.sleep(poll_interval)

    pytest.fail(f"Job {jobid} did not finish within {timeout}s")


logging.info("Performing REST-API request tests for stemweb\n")

### make sure that pytest is working properly in our project:
def test_always_passes():
    assert True


@pytest.mark.xfail(
                reason="OK, set to always fail",
                strict=True,
            )
def test_always_fails():
    assert False            


@pytest.mark.parametrize(
    "fixture_name, expected_timeout",
    [
        ("03_nnet", 15),
        ("04_do_rhm_dev", 25),
        ("05_do_nj_dev", 15),
        pytest.param(
            "06_rhm_dev_neverending", 25,
            marks=pytest.mark.xfail(
                reason="OK, expected to never finish and must hit timeout",
                strict=True,
            ),
        ),
    ],
    ids=["NeighbourNet", "RHM", "NeighborJoining", "rhm_neverending"]
)

def test_algorithms(app, fixture_name, expected_timeout):
    response = app.make_fixture_request(fixture_name)
    assert response["status"] == 1

    jobstatus = wait_for_job_finished(app, response["jobid"], timeout=expected_timeout)
    assert jobstatus["status"] == 0
