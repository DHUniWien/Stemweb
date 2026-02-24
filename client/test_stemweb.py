import os
import time
import logging
import pytest
import subprocess
from stemweb_pytest_client import app


#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s-%(message)s')
#logging.basicConfig(level=logging.DEBUG, filename='/src/app/testingClient.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')

"""
Basic functional & integration tests for stemweb, using 3 different algorithms.
Send requests to the stemweb service using the respective test data in `client/requests`.
Stemweb returns responses in json format.
"""

CI_TIMEOUT_FACTOR = 1.5 if os.getenv("CI") else 1.0     # because CI/github actions might have some delays
                                                        # GitHub Actions automatically sets: CI=true 
#logging.info(f"CI_TIMEOUT_FACTOR = {CI_TIMEOUT_FACTOR}\n")

def wait_for_job_finished(app, jobid, timeout, poll_interval=1):
    start = time.time()
    while time.time() - start < timeout:
        jobstatus = app.query_job(jobid)
        if jobstatus["status"] == 0:
            return jobstatus
        time.sleep(poll_interval)

    pytest.fail(f"Job {jobid} did not finish within {timeout} seconds")



logging.info("Performing REST-API request tests for stemweb\n")

### make sure that pytest is working properly in our project:
def test_always_passes():
    assert True


#@pytest.mark.xfail(
#                reason="OK, set to always fail",
#                strict=True,
#            )
#def test_always_fails():
#    assert False            


@pytest.mark.parametrize(
    "fixture_name, expected_timeout",
    [
        ("03_nnet", 15),
        ("04_do_rhm_dev", 25),
        ("05_do_nj_dev", 15)
    ],
    ids=["NeighbourNet", "RHM", "NeighborJoining"]
)

def test_algorithms(app, fixture_name, expected_timeout):
    response = app.make_fixture_request(fixture_name)
    assert response["status"] == 1

    effective_timeout = expected_timeout * CI_TIMEOUT_FACTOR
    jobstatus = wait_for_job_finished(app, response["jobid"], timeout=effective_timeout)
    assert jobstatus["status"] == 0



@pytest.fixture
def wait_for_log_content():
    """
    Wait for a specific line/content to appear in a Docker container's log.

    Usage,e.g:
        wait_for_log_content(container="stemweb-stemweb-1",
                     text="SIGKILL",
                     timeout=90)
    """

    def _wait(container, text, timeout, since="1m"):
        """
        We need this nested/inner function because Pytest fixtures cannot accept dynamic arguments at call time.
        It allows this pattern:
        fixture → returns function → test calls this function with arguments

        outer function wait_for_log_content() = fixture
        inner function _wait = callable used by the test
        """

        cmd = ["docker", "logs", f"--since={since}", "--follow", container]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line buffered
        )

        start = time.time()

        try:
            while True:
                if time.time() - start > timeout:
                    pytest.fail(f"Did not see '{text}' in logs of {container} before timeout")
                    return False
                line = process.stdout.readline()
                if not line:
                    continue
                #logging.info(f"Read log line: {line.strip()}")
                if text in line:
                    return line.strip()

        finally:    ### clean up
            process.terminate()
            process.wait()

    return _wait


def test_algorithm_rhm_neverending(app, wait_for_log_content, timeout=90):
    response = app.make_fixture_request("06_rhm_dev_neverending")
    assert response["status"] == 1
    effective_timeout = timeout * CI_TIMEOUT_FACTOR
    try:
        found_sigkill = wait_for_log_content(
            container="stemweb-stemweb-1",      ###  if the new "docker compose" command is used
            #container="stemweb_stemweb_1",     ###  if the old "docker-compose" command is used
            text="signal 9 (SIGKILL)",
            timeout=effective_timeout
        )
        if found_sigkill:
            jobstatus = app.query_job(response["jobid"])
            assert jobstatus["status"] == 3   ### status celery task timeout
            pytest.xfail(reason="RHM with this given data never finishes but was killed correctly by Celery hard timeout")
        # else:   ### is already handled in _wait()-timeout
        #   pytest.fail(f"Did not see '{text}' in logs of {container} before timeout")
    except Exception as e:
        raise RuntimeError(f"{e}"
    )

    
