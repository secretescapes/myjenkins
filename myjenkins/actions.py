import logging

from requests.exceptions import HTTPError
from jenkinsapi.custom_exceptions import NotFound

logger = logging.getLogger('myjenkins') # FIXME Should use __name__


def find_recent_builds(job):
    """Return a list of most recent builds for a job."""
    builds = _find_recent_builds(job)
    builds = filter(lambda b: not b.is_running(), builds)
    builds = filter(lambda b: b.get_status() in ['SUCCESS', 'UNSTABLE'],
                    builds)

    return builds


def _find_recent_builds(job):
    for _id in job.get_build_ids():
        try:
            yield job.get_build_metadata(_id)
        except (NotFound, HTTPError):
            pass # FIXME Random 500s from Jenkins


def set_build_description(jenkins, build, description):
    """Set a build's description (which appears in the UI)."""
    jenkins.requester.post_and_confirm_status(
        '{0}/submitDescription'.format(build.baseurl),
        data='description={0}&Submit=Submit'.format(description),
        valid=[302, 200],
    )
