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

    # Nix install (it's automatically isolated, and the suggested approach, especially if you don't have python3 installed or don't know what is a virtualenv)

    nix-env -f default.nix -i

    # Nix development shell (use py.test directly rather than tox)

    nix-shell

    # Full development installation (including pandas, a library using native code needed for the flakyness reports)

    pip install -e .[pandas]

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

Rerun failed tests of build #2 of mypipeline's master branch (up to 3 times).

    myjenkins retry mypipeline/master 2
