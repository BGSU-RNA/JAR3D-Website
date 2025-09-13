from django.urls import path, re_path
from app import views

from django.conf import settings
from django.conf.urls.static import static

# ChatGPT suggests that \w{8} below may not match lowercase letters, and suggests:
# re_path(r'^result/(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/$', views.result, name='result'),
# If that becomes a problem, then we will know what to do.
# re_path(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', views.result, name='result'),

urlpatterns = [
    path('process_input/', views.process_input, name='process_input'),
    re_path(r'^result/(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/(?P<loopid>\d+)/(?P<motifgroup>[^\s/]+)/?', views.single_result, name='single_result'),
    re_path(r'^result/(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/(?P<loopid>\d+)/?', views.all_result, name='all_result'),
    re_path(r'^result/(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/?', views.result, name='result'),
    re_path(r'^refine/(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/?', views.home, name='refine'),
    re_path(r'^result/(?P<uuid>RF[0-9]{5}-[0-9]+\.[0-9]+)/(?P<loopid>\d+)/(?P<motifgroup>[^\s/]+)/?', views.single_result, name='single_result'),
    re_path(r'^result/(?P<uuid>RF[0-9]{5}-[0-9]+\.[0-9]+)/(?P<loopid>\d+)/?', views.all_result, name='all_result'),
    re_path(r'^result/(?P<uuid>RF[0-9]{5}-[0-9]+\.[0-9]+)/?', views.result, name='result'),
    re_path(r'^refine/(?P<uuid>RF[0-9]{5}-[0-9]+\.[0-9]+)/?', views.home, name='refine'),
    re_path(r'^rfam/(?P<version>\d+\.\d+)/(?P<motifgroup>[^\s/]+)/?', views.motif_hits, name='motif_hits'),
    re_path(r'^rfam/(?P<version>\d+\.\d+)/?', views.rfam_search, name='rfam_search'),
    re_path(r'^rfam/?', views.rfam_search, name='rfam_search'),
    path('', views.home, name='home'),
]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# last line above puts full URLs for static files, instead of file system references



# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
# test comment

# old code something like this:
# urlpatterns = [
#     url(r'^process_input$', 'jar3d.app.views.process_input'),
#     url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'jar3d.app.views.result'),
#     url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<loopid>\d)/(?P<motifgroup>.*)/$', 'jar3d.app.views.single_result'),
#         url(r'^result/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<loopid>\d)/$', 'jar3d.app.views.all_result'),
#     url(r'^refine/(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', 'jar3d.app.views.home', name='refine'),
#     url(r'^$', 'jar3d.app.views.home', name='home'),

#     # Uncomment the admin/doc line below to enable admin documentation:
#     # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

#     # Uncomment the next line to enable the admin:
#     # url(r'^admin/', include(admin.site.urls)),
# ]
