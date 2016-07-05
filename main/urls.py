from django.conf.urls import patterns, url

from main import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^help.html$', views.helper, name='help'),
    url(r'^search$', views.search, name='search'),
    url(r'^search&keyword=(?P<keyword>.+)$', views.search_keyword, name='search_keyword'),
    url(r'^company/(?P<company>.+)$', views.search_company, name='search_company'),
    url(r'^listpub$', views.listing, name='listing'),    
    url(r'^explore$', views.explore, name='explore'),

)
        