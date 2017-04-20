import pytest
from myjenkins.testing import jenkins_mocks
from myjenkins.log import setup_logging


def pytest_configure():
    setup_logging(2)


@pytest.fixture
def client():
    """Fixture. Returns a Jenkins client which exposes a job which has
    builds and subbuilds."""
    # create three jobs
    top_level_job = jenkins_mocks.create_job('top')
    sub_job_1 = jenkins_mocks.create_job('sub_1')
    sub_job_2 = jenkins_mocks.create_job('sub_2')

    # each having one build
    top_level_build = jenkins_mocks.create_build(1)
    sub_job_1_build = jenkins_mocks.create_build(1)
    sub_job_2_build = jenkins_mocks.create_build(1)

    # pretend that the build for the top level job triggered the sub jobs
    top_level_build._data = {
        'subBuilds': [
            {'jobName': 'sub_1', 'buildNumber': 1},
            {'jobName': 'sub_2', 'buildNumber': 1},
        ]
    }

    # associate each job which its respective builds
    top_level_job._builds = {1: top_level_build}
    sub_job_1._builds = {1: sub_job_1_build}
    sub_job_2._builds = {1: sub_job_2_build}

    # create a client which contains those jobs
    client = jenkins_mocks.create_client()
    client._jobs = {
        'top': top_level_job,
        'sub_1': sub_job_1,
        'sub_2': sub_job_2,
    }

    return client
