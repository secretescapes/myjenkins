import logging
from itertools import islice
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
from .picker import Branch, Revision
from .util import format_dict

logger = logging.getLogger('myjenkins') # FIXME Should use __name__


class Runner(object):
    """Runs visitors concurrently."""

    def __init__(self, branch=None, revision=None, hard_limit=-1, soft_limit=-1, concurrency=-1):
        self.concurrency = concurrency if concurrency > 0 else cpu_count()
        self.pool = Pool(self.concurrency)
        self.hard_limit = hard_limit
        self.soft_limit = soft_limit
        self.requirements = []

        if branch:
            self.requirements.append(Branch(branch))

        if revision:
            self.requirements.append(Revision(revision))

    def run(self, visitor, builds, flatten=True):
        if self.hard_limit > 0:
            builds = islice(builds, self.hard_limit)

        iterator = iter(builds)
        no_soft_limit = self.soft_limit <= 0

        logger.info('Starting run ({0})'.format(format_dict(self.__dict__)))

        while no_soft_limit or visitor.matches < self.soft_limit:
            next_batch = list(islice(iterator, self.concurrency))
            if not next_batch:
                break # Exhausted all

            buckets = self.pool.map(
                lambda x: visitor.visit(x, self.requirements), next_batch)
            logger.debug('Finished batch ({0} matched so far)'.format(visitor.matches))

            for result_bucket in buckets:
                if flatten:
                    yield from result_bucket
                else:
                    yield result_bucket
