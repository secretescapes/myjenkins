from collections import OrderedDict
import numpy as np


def nflakes(series):
    return np.sum(x for x in np.ediff1d(series) if x > 0)


def flaky_breakdown(frame, min_builds=2, group_by_test=False):
    """Generate a breakdown of flaky tests by branch and revision."""
    aggregations = OrderedDict([
        ('success', {'n': 'sum'}),
        ('failure', OrderedDict([
            ('n', 'sum'),
            ('flakes', nflakes),
        ])),
    ])

    group_by = ['test', 'branch', 'revision'] if group_by_test else ['branch', 'revision', 'test']

    # Note: groupby preserves order (which is needed for ediff1d)
    frame = frame.sort_values('timestamp', ascending=False)
    frame = frame.groupby(group_by).agg(aggregations)

    frame['total'] = frame['success', 'n'].add(frame['failure', 'n'])
    frame = frame[frame['total'] >= min_builds]
    frame = frame[frame['failure', 'flakes'] > 0]

    # Calculate flakiness value (total runs / number of test status changes)
    flakes = frame['failure', 'flakes']

    frame['flakiness %'] = np.round(flakes.div(frame['total']).mul(200), decimals=1)
    frame = frame.drop([('failure', 'flakes')], axis=1)

    return frame
