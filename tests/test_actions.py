import pytest
from mock import Mock
from requests.exceptions import HTTPError
from jenkinsapi.constants import STATUS_ABORTED, STATUS_FAIL, STATUS_ERROR
from jenkinsapi.custom_exceptions import NotFound
from myjenkins.actions import find_recent_builds
from myjenkins.testing import jenkins_mocks


@pytest.fixture
def job():
    """Fixture. Returns a job which has 3 builds."""
    job = jenkins_mocks.create_job('foo')
    job._builds = {i + 1: jenkins_mocks.create_build(i + 1) for i in range(3)}

    return job


def test_find_recent_builds(job):
    """Return builds of a job"""
    assert [b.buildno for b in find_recent_builds(job)] == [1, 2, 3]


@pytest.mark.parametrize('status', [STATUS_ABORTED, STATUS_FAIL, STATUS_ERROR])
def test_ignore_unclean_run(job, status):
    """Ignore unclean runs"""
    ignored = job._builds[1]
    ignored.get_status.return_value = status

    assert ignored not in find_recent_builds(job)


def test_ignore_running(job):
    """Ignore aborted jobs"""
    ignored = job._builds[1]
    ignored.is_running.return_value = True

    assert ignored not in find_recent_builds(job)


@pytest.mark.parametrize('exception', [NotFound, HTTPError])
def test_ignore_abnormal_jobs(job, exception):
    """Skip builds which 500 or have no job history"""
    job.__getitem__ = Mock(side_effect=exception)
    job.get_build_metadata = Mock(side_effect=exception)

    assert not list(find_recent_builds(job))
