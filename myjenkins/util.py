

class TestStatus(object):
    SUCCESS, FAILURE = list(range(2))


def test_status(test):
    """Return the state of a test."""
    return TestStatus.SUCCESS if test.failedSince <= 0 else TestStatus.FAILURE


def format_dict(d):
    return ', '.join('{0}={1}'.format(k, repr(v)) for k, v in
                     d.items())


def ltrunc(s, max_length):
    return s if len(s) < max_length else '..' + s[-max_length + 3:]


class PrettyRepr(object):
    def __repr__(self):
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   format_dict(self.__dict__))
