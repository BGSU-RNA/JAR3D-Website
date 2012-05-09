from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
# test comment

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'JAR3Doutput.views.home', name='home'),
    # url(r'^JAR3Doutput/', include('JAR3Doutput.foo.urls')),

    url(r'^home$', 'JAR3Dresults.views.home'),
    url(r'^process_input$', 'JAR3Dresults.views.process_input'),
    url(r'^JAR3Doutput/Results/(?P<query_id>\S+)/$', 'JAR3Dresults.views.results'),
    url(r'^JAR3Doutput/GroupResults/(?P<query_id>\S+)/(?P<group_num>\S+)/$', 'JAR3Dresults.views.group_results'),

    url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'JAR3Dresults.views.result'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
