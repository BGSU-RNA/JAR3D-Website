from django.conf.urls import patterns, url

urlpatterns = patterns('web_jar3d',

    url(r'^process_input$', 'views.process_input'),

    url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$',
        'views.result'),

    url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<loopid>\d)/(?P<motifgroup>.*)/$',
        'views.single_result'),

    url(r'^refine/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$',
        'views.home', name='refine'),

    url(r'^$', 'views.home', name='home'),
)
