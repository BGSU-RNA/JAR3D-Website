from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
# test comment

urlpatterns = patterns('',

    url(r'^process_input$', 'JAR3Dresults.views.process_input'),
    url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'JAR3Dresults.views.result'),
    url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<loopid>\d)/(?P<motifgroup>.*)/$', 'JAR3Dresults.views.single_result'),
    url(r'^refine/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'JAR3Dresults.views.home', name='refine'),
    url(r'^$', 'JAR3Dresults.views.home', name='home'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
