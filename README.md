myjenkins
=========

CLI for Jenkins. Requires Python 3.

Instructions
------------
Test with:

    pip3 install tox
    tox

Install with:

    # Normal install
    pip3 install git+ssh://git@github.com/secretescapes/myjenkins.git@master

    # Development install
    pip3 install -e .


Run with:

    myjenkins


Examples
--------
Setup environment variables.

    # See <jenkins URL>/user/<your username>/configure for these details
    export JENKINS_USERNAME=joe.bloggs@example.com
    export JENKINS_TOKEN=...
    export JENKINS_HOSTNAME=http://jenkins.example.com

Generate a flaky test report.

    myjenkins health myjob # Single / multi-job
    myjenkins health mypipeline/master # Pipelines

Rerun failed tests of build #2 of mypipeline's master branch.

    myjenkins failures mypipeline/master 2
