from itertools import chain
import copy
import logging
from requests.exceptions import HTTPError
from jenkinsapi.custom_exceptions import NotFound
from .util import PrettyRepr, TestStatus, test_status
from .picker import Branch, Revision

logger = logging.getLogger('myjenkins') # FIXME Should use __name__


class BranchState(PrettyRepr):
    """The state of one branch of the tree traversal."""

    def __init__(self, requirements=None, trackers=None, depth=-1):
        self.depth = depth
        self.requirements = requirements or []
        self.trackers = trackers or []

    def advance(self, next_build):
        next_state = copy.deepcopy(self)
        next_state.depth += 1

        for p in chain(next_state.requirements, next_state.trackers):
            p.evaluate(next_build)

        logger.debug('Evaluated {0}: {1}'.format(next_build, next_state))

        return next_state


class BuildVisitor(object):
    """Base class. Visits nodes of a build tree."""

    def __init__(self, client, trackers=None):
        self.client = client
        self.trackers = trackers or []
        self.reset()

    def reset(self):
        self.matches = 0

    def visit(self, root, requirements=None):
        state = BranchState(requirements, self.trackers).advance(root)

        return list(self._visit(root, state))

    def _visit(self, build, state):
        logger.debug('{0} {1}'.format('*' * (state.depth + 1), build))

    def collect(self, build, state):
        logger.info('Collecting {0}'.format(build))
        self.matches += 1

        return build

    def can_collect(self, build, state):
        return all(p.has_match for p in state.requirements)

    def children(self, build):
        for sb in build._data.get('subBuilds', []):
            try:
                yield self.client[sb['jobName']].get_build_metadata(sb['buildNumber'])
            except (NotFound, HTTPError):
                pass # FIXME Random 500s from Jenkins


class TestCollector(BuildVisitor):
    """Collects all test results for a build run."""

    def _visit(self, build, state):
        super(TestCollector, self)._visit(build, state)

        children = list(self.children(build))
        if children:
            for child in children:
                yield from self._visit(child, state.advance(child))
        elif self.can_collect(build, state):
            yield from self.collect(build, state)

    def collect(self, build, state):
        super(TestCollector, self).collect(build, state)
        return (v for k, v in build.get_resultset().items())

    def can_collect(self, build, state):
        return build.has_resultset() and \
            super(TestCollector, self).can_collect(build, state)


class ExtendedTestCollector(TestCollector):
    """As `TestCollector`, but also includes the test's revision, branch and timestamp."""

    def __init__(self, client):
        super(TestCollector, self).__init__(client, (Branch(), Revision()))

    def collect(self, build, state):
        for test in super(ExtendedTestCollector, self).collect(build, state):
            yield (test, ) + tuple(t.found_value for t in state.trackers) + (build.get_timestamp(), )


class FailedTestCollector(TestCollector):
    """As `TestCollector`, but only collects failed tests."""

    def visit(self, root, requirements=None):
        return [t for t in super(FailedTestCollector, self).visit(root) if test_status(t) == TestStatus.FAILURE]


class SubbuildCollector(BuildVisitor):
    """Collects all subbuilds for a test."""

    def _visit(self, build, state):
        super(SubbuildCollector, self)._visit(build, state)

        if self.can_collect(build, state):
            yield self.collect(build, state)

        for child in self.children(build):
            yield from self._visit(child, state.advance(child))

    def can_collect(self, build, state):
        return state.depth > 0 and \
            super(SubbuildCollector, self).can_collect(build, state)
