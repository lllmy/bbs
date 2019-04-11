"""bbs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.static import serve
from django.conf import settings
from blog import views
from blog import urls as blog_urls
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', views.Login.as_view()),  # 登录
    url(r'^login2/$', views.login2),
    url(r'^pcgetcaptcha/$', views.pcgetcaptcha),
    url(r'^index/$', views.Index.as_view()),  # 首页
    url(r'^v-code/$', views.v_code),          # 验证码
    url(r'^reg/$', views.RegView.as_view()),          # 验证码
    # 给用户上传文件 配置一个处理的路由
    url(r'^media/(?P<path>.*)', serve, {"document_root": settings.MEDIA_ROOT}),
    url(r'^logout',views.logout1),
    # 这个是我自己的
    # url(r'^every/$',views.every),
    # 这个是模仿老师的
    url(r'^home/$',views.home),
    # 配一个二级路由
    url(r'blog/',include(blog_urls)),
    # 点赞
    url(r'^updown/$', views.updown),
    # 评论
    url(r'^comment/$', views.comment),
]
