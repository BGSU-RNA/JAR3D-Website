from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'JAR3Doutput.views.home', name='home'),
    # url(r'^JAR3Doutput/', include('JAR3Doutput.foo.urls')),
                       
    url(r'^JAR3Doutput/Results/(?P<query_id>\S+)/$', 'JAR3Dresults.views.results'),
    url(r'^JAR3Doutput/GroupResults/(?P<query_id>\S+)/(?P<group_num>\S+)/$', 'JAR3Dresults.views.group_results'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
