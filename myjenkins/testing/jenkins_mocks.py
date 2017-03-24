from types import MethodType as M
from mock import Mock
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.job import Job
from jenkinsapi.build import Build


def create_job(name):
    """Creates a configurable mock job."""
    job = Mock(dir(Job) + ['_builds'], name='Job-{0}'.format(name))
    job.configure_mock(_builds={})

    job.name = name
    job.get_build_ids = M(lambda self: list(self._builds.keys()), job)
    job.__getitem__ = M(lambda self, _, k: self._builds[k], job)
    job.get_build_metadata = M(lambda self, k: self._builds[k], job)

    return job


def create_build(buildno):
    """Creates a configurable mock build."""
    build = Mock(dir(Build) + ['_data'], name='Build-{0}'.format(buildno))

    build.buildno = buildno
    build.has_resultset = M(
        lambda self: isinstance(self.get_resultset(), dict), build)

    build.get_status.return_value = 'SUCCESS'
    build.get_params.return_value = {}
    build.get_revision.return_value = ''
    build.is_running.return_value = False
    build._data = {}

    return build


def create_client():
    """Creates a configurable mock Jenkins client."""
    client = Mock(dir(Jenkins) + ['_jobs'], name='Client')
    client.configure_mock(_jobs={})

    client.__getitem__ = lambda self, k: self._jobs[k]

    return client
