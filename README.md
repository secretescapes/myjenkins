myjenkins
=========

Search for flaky tests in Jenkins.

Instructions
------------
Test with:

    tox

Install with:

    # Normal install
    pip install git+https://github.com/secretescapes/myjenkins

    # Development install
    pip install -e .


Run with:

    myjenkins


Examples
--------
Setup environment variables.

    # See <jenkins URL>/user/<your username>/configure for these details
    export JENKINS_USERNAME=joe.bloggs@example.com
    export JENKINS_TOKEN=...
    export JENKINS_HOSTNAME=jenkins.example.com


Generate a flaky test report.

    myjenkins health myjob # Single / multi-job
    myjenkins health mypipeline/master # Pipelines

Rerun failed tests of build #2 of mypipeline's master branch.

    myjenkins failures mypipeline/master 2
