from django.conf.urls import url
from blog import views

urlpatterns = [
    # url(r'^(\w+)/$', views.every),
    url(r'^backend/$', views.backend),
    url(r'^add_article/$', views.add_article),
    url(r'^upload/$', views.upload),
    url(r'^(\w+)/$', views.home),
    url(r'^(\w+)/p/(\d+)', views.article),
    url(r'^(\w+)/(category|tag|archive)/(.*)/$', views.home),
]