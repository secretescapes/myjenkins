from mock import Mock
from jenkinsapi.result import Result
from myjenkins.picker import Branch, Revision
from myjenkins.visitor import SubbuildCollector, TestCollector


def _add_tests(client):
    tests_a = [Result(className='com.foo', name='foo', status='PASSED')]
    tests_b = [Result(className='com.bar', name='bar', status='PASSED')]
    tests_c = [Result(className='com.baz', name='baz', status='PASSED')]

    top_build = client['top'][1]
    top_build.get_resultset = Mock(return_value={t.identifier(): t for t in tests_a})

    sub_build_1 = client['sub_1'][1]
    sub_build_1.get_resultset = Mock(return_value={t.identifier(): t for t in tests_b})

    sub_build_2 = client['sub_2'][1]
    sub_build_2.get_resultset = Mock(return_value={t.identifier(): t for t in tests_c})


def _add_requirements(client):
    client['top'][1].get_params.return_value = {'BRANCH_NAME': 'foo'}
    client['sub_1'][1].get_revision.return_value = 'match-me'


def test_matches_counter(client):
    """Increments ``matches`` counter"""
    v = SubbuildCollector(client)
    v.visit(client['top'][1])

    assert v.matches == 2


def test_find_subbuilds(client):
    """Find subbuilds"""
    assert SubbuildCollector(client).visit(client['top'][1]) \
        == [client['sub_1'][1], client['sub_2'][1]]


def test_find_subbuilds_with_requirements(client):
    """Find subbuilds with requirements"""
    _add_requirements(client)

    v = SubbuildCollector(client)
    requirements = [Branch('foo'), Revision('match-me')]

    assert set(v.visit(client['top'][1], requirements)) == set([client['sub_1'][1]])


def test_extract_tests(client):
    """Extract tests"""
    _add_tests(client)

    assert set(t.name for t in TestCollector(client).visit(client['top'][1])) == \
        set(['bar', 'baz'])


def test_extract_with_requirements(client):
    """Extract tests from leaf nodes"""
    _add_tests(client)
    _add_requirements(client)

    requirements = [Branch('foo'), Revision('match-me')]

    assert set(t.name for t in TestCollector(client).visit(client['top'][1], requirements)) == \
        set(['bar'])
