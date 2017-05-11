myjenkins
=========

CLI for Jenkins. Requires Python 3.

Installation
------------
Install with:

    pip3 install git+ssh://git@github.com/secretescapes/myjenkins.git@stable#egg=myjenkins[pandas]

Or with Nix:

    nix-env -f https://github.com/secretescapes/myjenkins/archive/stable.tar.gz -i


Run with (see Examples section):

    myjenkins
    
    
Upgrade
--------
For pip installs:

    pip3 install git+ssh://git@github.com/secretescapes/myjenkins.git@stable#egg=myjenkins[pandas] --upgrade

Development
-----------

Test with:

    pip3 install tox
    tox

You can get a development shell with Nix:

    cd myjenkins
    nix-shell

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

Find all failed tests and related artifacts for build #10.

    myjenkins summary mypipeline/master 10
