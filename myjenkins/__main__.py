from collections import namedtuple
from functools import wraps
import click
from jenkinsapi.jenkins import Jenkins
from .validation import positive_nonzero
from .actions import find_recent_builds, set_build_description
from .util import TestStatus, test_status
from .runner import Runner
from .output import output_frame
from . import visitor, log


def requires_pandas(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            import pandas as pd
        except ImportError:
            raise click.UsageError('pandas must be installed to run this command')

        pd.set_option('display.max_colwidth', 140)
        f(*args, **kwargs)

    return wrapper


@click.group()
@click.pass_context
@click.option('-h', '--hostname', envvar='JENKINS_HOSTNAME', required=True)
@click.option('-u', '--username', envvar='JENKINS_USERNAME')
@click.option('-p', '--token', envvar='JENKINS_TOKEN')
@click.option('-v', '--verbose', count=True)
@click.option('-b', '--branch', help='restrict collection by branch')
@click.option('-r', '--revision', help='restrict collection by revision')
@click.option('-s', '--soft-limit', type=int, default=-1, help='end after this many matches')
@click.option('-l', '--hard-limit', type=int, default=50, help='end after this many traversals')
@click.option('-k', '--concurrency', type=int, default=-1, help='number of workers')
def myjenkins(ctx, hostname, username, token, verbose, **config):
    log.setup_logging(verbose)

    ctx.obj = namedtuple('obj', ['client', 'runner'])(Jenkins(hostname, username, token),
                                                      Runner(**config))


@myjenkins.command()
@click.pass_obj
@click.argument('job')
@click.argument('build_id', type=int)
@click.option('-m', '--max-attempts', type=int, default=3, callback=positive_nonzero,
              help='give up after this many attempts')
def retry(o, job, build_id, max_attempts):
    """Rerun failed tests for a build and its children."""
    job = o.client[job]
    cur = original = job[build_id]
    attempt_n = 0

    while True:
        results = set(r.className for r in visitor.FailedTestCollector(o.client).visit(cur))
        if not results or attempt_n >= max_attempts:
            break

        # Retry the failed tests
        print('Retrying {0} (attempt {1} of {2}; {3} tests still failing)...'.format(original,
                                                                                     attempt_n + 1,
                                                                                     max_attempts,
                                                                                     len(results)))

        queued = job.invoke(build_params={'TEST_WHITELIST': '\n'.join(results)})
        queued.block_until_building()
        triggered = job[queued.get_build_number()] # FIXME queued.get_build() does not work with folders

        set_build_description(o.client,
                              triggered,
                              'Retry of #{0}\'s failed tests'.format(cur.buildno))

        print('Waiting for {0} ...'.format(triggered.baseurl))
        triggered.block_until_complete()
        triggered.poll()

        # Retry those that failed again, again
        cur = triggered
        attempt_n += 1

    if attempt_n == 0:
        raise click.BadParameter('No tests have failed for that build', param_hint='build_id')
    elif results:
        print('Failure: {0} test(s) are still failing after {1} attempts'.format(len(results), attempt_n + 1))
    else:
        print('Success: all tests passed after {0} attempt(s)'.format(attempt_n + 1))


@myjenkins.command()
@click.pass_obj
@click.argument('job')
@click.option('-m', '--min-builds', default=2, help='only mark as flaky if >= N builds seen')
@click.option('-t', '--time-series', is_flag=True)
@click.option('-f', '--freq', default='D')
@click.option('-h', '--html', is_flag=True)
@click.option('-g', '--group-by-test', is_flag=True)
@requires_pandas
def health(o, job, **kwargs):
    """Identify flaky tests."""
    import pandas as pd
    from .process import flaky_breakdown, flaky_time_series

    builds = find_recent_builds(o.client[job])

    def process(result):
        test, branch, revision, timestamp = result
        status = test_status(test)
        return (test.identifier(),
                str(branch or '?'),
                str(revision or '?'),
                int(status == TestStatus.SUCCESS),
                int(status == TestStatus.FAILURE),
                timestamp)

    vi = visitor.ExtendedTestCollector(o.client)
    results = list(map(process, o.runner.run(vi, builds)))

    if not results:
        return

    frame = pd.DataFrame.from_records(results,
                                      columns=('test', 'branch', 'revision', 'success', 'failure', 'timestamp'))

    if kwargs['time_series']:
        frame = flaky_time_series(frame, **kwargs)
    else:
        frame = flaky_breakdown(frame, **kwargs)

        print('Found {0} flaky tests (of {1} total tests) affecting {2} branches '
              '(based on {3} test runs from {4} builds)'
              .format(frame.index.get_level_values('test').nunique(),
                      len(set(t[0] for t in results)),
                      frame.index.get_level_values('branch').nunique(),
                      len(results),
                      vi.matches))

    output_frame(frame, **kwargs)


main = myjenkins

if __name__ == '__main__':
    main()
