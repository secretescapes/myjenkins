from myjenkins.picker import Picker, Branch, Revision
from myjenkins.testing.jenkins_mocks import create_build


class DummyPicker(Picker):
    def pick(self, build):
        return build


def test_remains_matched():
    c = DummyPicker()
    assert not c.has_match

    c.evaluate('foo')
    assert c.has_match

    c.evaluate('bar')
    assert c.has_match


def test_retains_found_on():
    c = DummyPicker()
    c.evaluate('foo')
    c.evaluate('bar')

    assert c.found_on == 'foo'


def test_branch():
    build = create_build('a')
    build.get_params.return_value = {'BRANCH_NAME': 'foo'}

    picker = Branch('foo')
    picker.evaluate(build)
    assert picker.has_match


def test_revision():
    build = create_build('a')
    build.get_revision.return_value = 'foo'

    picker = Revision('foo')
    picker.evaluate(build)
    assert picker.has_match
