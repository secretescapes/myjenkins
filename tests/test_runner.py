from myjenkins.runner import Runner
from myjenkins.visitor import SubbuildCollector


def test_runner(client):
    visitor = SubbuildCollector(client)
    results = Runner().run(visitor, [client['top'][1]])

    assert set(results) == set([
        client['sub_1'][1],
        client['sub_2'][1]
    ])
