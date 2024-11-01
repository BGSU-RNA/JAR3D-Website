"""
WSGI config for jar3d project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""

import os
import sys

# sys.path.insert(0, os.path.dirname(__file__))
# sys.path.insert(1, os.path.join(os.path.dirname(__file__), "JAR3Doutput"))
# os.environ["DJANGO_SETTINGS_MODULE"] = "JAR3Doutput.settings"

# # This application object is used by any WSGI server configured to use this
# # file. This includes Django's development server, if the WSGI_APPLICATION
# # setting points here.
# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()

# Add project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(1, '/var/www/jar3d/')
sys.path.insert(2, '/usr/local/pipeline/RNAStructure')

# Set the Django settings module environment variable
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import the WSGI application
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception as e:
    # You can log errors here, or print them for debugging purposes
    print(f"WSGI application error: {e}")
    raise
