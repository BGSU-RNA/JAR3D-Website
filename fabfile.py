from __future__ import with_statement

from fabric.api import task
from fabric.api import run
from fabric.api import local
from fabric.api import cd
from fabric.api import env
from fabric.api import prefix


env.hosts = ["api@rna.bgsu.edu"]
env.virtualenv = "api"
env.base = '~/deploy'

# Differ between prod and dev
env.app_name = 'jar3d-dev'
env.branch = 'develop'


def common():
    env.app = '%s/apps/%s' % (env.base, env.app_name)


@task
def prod():
    env.branch = 'master'
    env.app_name = 'jar3d'


@task
def merge():
    local("git checkout master")
    local("git merge master develop")


@task
def deploy():
    common()

    with prefix("workon %s" % env.virtualenv):
        with cd(env.app):
            run("git pull origin %s" % env.branch)
            run("python JAR3Doutput/manage.py collectstatic --noinput")

        with cd(env.base):
            run("supervisorctl -c conf/supervisord.conf restart %s:*" %
                env.app_name)


@task
def status():
    with cd(env.base):
            run("supervisorctl -c conf/supervisord.conf status %s:*" %
                env.app_name)
