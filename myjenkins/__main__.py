from collections import namedtuple
import click
import pandas as pd
from jenkinsapi.jenkins import Jenkins
from .actions import find_recent_builds, set_build_description
from .util import TestStatus, test_status
from .runner import Runner
from .process import flaky_breakdown, flaky_time_series
from .output import output_frame
from . import visitor, log


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
    pd.set_option('display.max_colwidth', 140)

    ctx.obj = namedtuple('obj', ['client', 'runner'])(Jenkins(hostname, username, token),
                                                      Runner(**config))


@myjenkins.command()
@click.pass_obj
@click.argument('job')
@click.argument('build_id', type=int)
@click.option('--dry-run', is_flag=True)
def failures(o, job, build_id, dry_run):
    """Rerun failed tests for a build and its children."""
    job = o.client[job]
    build = job[build_id]
    results = visitor.FailedTestCollector(o.client).visit(build)
    results = set(r.className for r in results)

    if results:
        for result in results:
            print(result)

        if not dry_run:
            print('Retrying {0}...'.format(build))

            queued_item = job.invoke(build_params={'TEST_WHITELIST': '\n'.join(results)})
            queued_item.block_until_building()

            # FIXME queued_item.get_build() does not work with folders
            set_build_description(o.client,
                                  job[queued_item.get_build_number()],
                                  'Retry of #{0}\'s failed tests'.format(build_id))
    else:
        print('No tests have failed for {0}'.format(build))


@myjenkins.command()
@click.pass_obj
@click.argument('job')
@click.option('-m', '--min-builds', default=2, help='only mark as flaky if >= N builds seen')
@click.option('-t', '--time-series', is_flag=True)
@click.option('-f', '--freq', default='D')
@click.option('-h', '--html', is_flag=True)
@click.option('-g', '--group-by-test', is_flag=True)
def health(o, job, **kwargs):
    """Identify flaky tests."""
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


@myjenkins.command()
@click.pass_obj
@click.argument('job')
def revisions(o, job):
    """List which revisions have been built."""
    builds = find_recent_builds(o.client[job])

    def process(subbuild):
        revision = subbuild.get_revision()
        if revision:
            return ((revision, 1)) # FIXME

    results = list(x for x in map(process, o.runner.run(visitor.SubbuildCollector(o.client), builds)) if x)

    frame = pd.DataFrame.from_records(results, columns=('revision', 'n'))
    frame = (frame
             .groupby('revision')
             .aggregate({'n': 'sum'})
             .sort_values('n', ascending=False))

    output_frame(frame)


main = myjenkins

if __name__ == '__main__':
    main()
