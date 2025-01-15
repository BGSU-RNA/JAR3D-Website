"""
Instead of using a queue, run the jar3d jar file directly.
score is for scoring one or more query loops against all JAR3D models
align is for aligning a set of sequences against one JAR3D model

The .jar files must have been made just for this task, and query the
database and probably write to the database afterward.
https://github.com/BGSU-RNA/JAR3D/tree/master/src/main/java/edu/bgsu/rna/jar3d
See webJAR3D.java.
"""

import logging
import os

from config import settings

logger = logging.getLogger(__name__)


def score(parameters):
    """
    Parse the parameters and run the jar3d jar file directly.
    """

    query_id = parameters['id']
    version = parameters['version']

    # this jar file runs JAR3D and writes results to the database
    jar = '/var/www/jar3d/jar/webJAR3D_server.jar'

    model_path = '/var/www/html/data/jar3d/models/'
    scope_file = 'all.txt'
    IL = os.path.join(model_path, 'IL', version, 'lib', scope_file)
    HL = os.path.join(model_path, 'HL', version, 'lib', scope_file)

    user     = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    database = settings.DATABASES['default']['NAME']

    # suppress output so it does not appear in syslog
    command = f'/usr/bin/java -Xmx500m -jar {jar} {IL} {HL} {query_id} {user} {password} {database} > /dev/null 2>&1'

    logger.debug('run_jar3d: score command: %s', command)

    exit_status = os.system(command)

    logger.debug('Ran os.system(command) and got exit_status: %s' % exit_status)

    return exit_status


def align(parameters):
    """
    parameters is a dictionary with these fields
    'id': uuid,
    'loop_id': loopid,

    !!!!!!!!!!! note that the java code seems to shift the loop number up by 1,
    so what we pass in is the loop number we want minus 1, then it shifts it up again

    'motif_group': motifgroup,
    'version': group_set.split('/')[0][2:]
    """
    uuid = parameters['id']
    loopid = parameters['loop_id']
    motifgroup = parameters['motif_group']
    version = parameters['version']

    # this jar file runs JAR3D and writes results to the database
    jar = '/var/www/jar3d/jar/jar3dCorr.jar'

    model_path = '/var/www/html/data/jar3d/models/'
    if motifgroup[0:2] == 'IL':
        models = os.path.join(model_path, 'IL', version, 'lib')
    elif motifgroup[0:2] == 'HL':
        models = os.path.join(model_path, 'HL', version, 'lib')

    user     = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    database = settings.DATABASES['default']['NAME']

    # suppress output so it does not appear in syslog
    command = f'/usr/bin/java -Xmx500m -jar {jar} {models} {motifgroup} {uuid} {loopid} {user} {password} {database} > /dev/null 2>&1'

    # put the command and output in the syslog for debugging
    command = f'/usr/bin/java -Xmx500m -jar {jar} {models} {motifgroup} {uuid} {loopid} {user} {password} {database}'
    print(command)

    # not sure where logger.debug actually goes
    logger.debug('run_jar3d: align command: %s', command)

    exit_status = os.system(command)

    logger.debug('Ran os.system(command) and got exit_status: %s' % exit_status)

    return exit_status
