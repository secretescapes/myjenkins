import logging
import os
from flask import Flask
from flask_restful import Api, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from jenkinsapi.jenkins import Jenkins
from . import log
from . import visitor
from flask_restful import Resource, reqparse
import pandas as pd
from .lookup import find_recent_builds
from .util import TestStatus, test_status
from .runner import Runner
from .process import flaky_breakdown

logger = logging.getLogger('myjenkins')
logging.getLogger('flask_cors').level = logging.DEBUG

app = Flask(__name__)
app.config.update(dict(
    VERBOSE=1,
    JENKINS_HOSTNAME=os.environ['JENKINS_HOSTNAME'],
    JENKINS_USERNAME=os.environ['JENKINS_USERNAME'],
    JENKINS_TOKEN=os.environ['JENKINS_TOKEN'],
    SQLALCHEMY_DATABASE_URI='sqlite:////tmp/test.db',
))
db = SQLAlchemy(app)
api = Api(app)
CORS(app)

log.setup_logging(app.config['VERBOSE'])
jenkins = Jenkins(app.config['JENKINS_HOSTNAME'],
                  app.config['JENKINS_USERNAME'],
                  app.config['JENKINS_TOKEN'])

parser = reqparse.RequestParser()
parser.add_argument('job', type=str)
parser.add_argument('branch', type=str)
parser.add_argument('revision', type=str)
parser.add_argument('hard_limit', type=int)


class ScanResource(Resource):
    """Jenkins result scan."""

    def get(self, scan_id):
        """Returns the result of a scan."""
        scan = Scan.query.filter_by(id=scan_id).first()
        if not scan:
            abort(404)

        return {
            'id': scan.id,
            'items': [{
                'branch': group.branch or '?',
                'revision': group.revision or '?',
                'tests': [{
                    'name': test.name,
                    'success': test.success,
                    'failure': test.failure,
                    'flakiness': test.flakiness,
                    'total': test.total
                } for test in group.tests.all()]
            } for group in scan.groups.all()]
        }, 200

    def post(self):
        """Triggers a new scan."""
        args = parser.parse_args()
        logger.info('Request args: {0}'.format(args))

        runner = Runner(branch=args.get('branch'), revision=args.get('revision'), hard_limit=args.get('hard_limit') or -1)
        builds = find_recent_builds(jenkins[args['job']])

        def process(result):
            test, branch, revision, timestamp = result
            status = test_status(test)
            return (test.identifier(),
                    str(branch) if branch else None,
                    str(revision) if branch else None,
                    int(status == TestStatus.SUCCESS),
                    int(status == TestStatus.FAILURE),
                    timestamp)

        vi = visitor.ExtendedTestCollector(jenkins)
        results = list(map(process, runner.run(vi, builds)))

        if not results:
            abort(204)

        frame = pd.DataFrame.from_records(results,
                                          columns=('test', 'branch', 'revision', 'success', 'failure', 'timestamp'))
        frame = flaky_breakdown(frame)

        scan = Scan()
        last_index = None

        for lol in frame.iterrows():
            index, values = lol
            if last_index is None or (index[:2] != last_index[:2]):
                last_index = tuple(index)[:2]
                group = ScanGroup(index[0], index[1], scan)
                db.session.add(group)

            result = TestResult(index[2],
                                int(values.success),
                                int(values.failure),
                                float(values.flakiness),
                                group)
            db.session.add(result)

        db.session.add(scan)
        db.session.commit()

        return {'id': scan.id}, 200


class Scan(db.Model):
    __tablename__ = 'scan'

    id = db.Column(db.Integer, primary_key=True)


class ScanGroup(db.Model):
    __tablename__ = 'scan_group'

    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(255))
    revision = db.Column(db.String(255))

    scan_id = db.Column(db.Integer, db.ForeignKey('scan.id'))
    scan = db.relationship('Scan', backref=db.backref('groups', lazy='dynamic'))

    def __init__(self, branch, revision, scan):
        self.branch = branch
        self.revision = revision
        self.scan = scan


class TestResult(db.Model):
    __tablename__ = 'test_result'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    success = db.Column(db.Integer)
    failure = db.Column(db.Integer)
    flakiness = db.Column(db.Float)

    scan_group_id = db.Column(db.Integer, db.ForeignKey('scan_group.id'))
    scan_group = db.relationship('ScanGroup', backref=db.backref('tests', lazy='dynamic'))

    def __init__(self, name, success, failure, flakiness, scan_group):
        self.name = name
        self.success = success
        self.failure = failure
        self.flakiness = flakiness
        self.scan_group = scan_group

    @property
    def total(self):
        return self.success + self.failure


api.add_resource(ScanResource, '/scan/', '/scan/<scan_id>')
