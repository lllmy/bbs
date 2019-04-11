import os
import random
from io import BytesIO
from blog import models
from bs4 import BeautifulSoup
from utils.geetest import GeetestLib
from utils.mypage import MyPage
from PIL import Image, ImageDraw, ImageFont                     # 专门用来返回验证码图片
from blog.forms import LoginForm, RegisterForm
from django.views import View
from django.contrib import auth
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Count,F
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, login, logout     # auth验证
# Create your views here.


# 请在官网申请ID使用，示例ID不可使用
pc_geetest_id = "b46d1900d0a894591916ea94ea91bd2c"
pc_geetest_key = "36fc3fe98530eea08dfc6ce76e3d24c4"

# 滑动验证码第一步的API,初始化一些参数用来校验滑动验证码
def pcgetcaptcha(request):
    user_id = 'test'
    gt = GeetestLib(pc_geetest_id, pc_geetest_key)
    status = gt.pre_process(user_id)
    request.session[gt.GT_STATUS_SESSION_KEY] = status
    request.session["user_id"] = user_id
    response_str = gt.get_response_str()
    return HttpResponse(response_str)


# 滑动验证码版本的登录
def login2(request):
    res = {"code": 0}
    if request.method == "POST":
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        status = request.session[gt.GT_STATUS_SESSION_KEY]
        user_id = request.session["user_id"]
        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)

        if result:
            # 滑动验证码校验通过
            username = request.POST.get('username')
            pwd = request.POST.get('password')
            print(username, pwd)
            user = auth.authenticate(username=username, password=pwd)
            if user:
                # 用户名密码正确
                auth.login(request, user)
            else:
                # 用户名或密码错误
                res["code"] = 1
                res["msg"] = "用户名或密码错误"

        else:
            # 滑动验证码校验失败
            res["code"] = 1
            res["msg"] = "验证码错误"
        return JsonResponse(res)

        # return HttpResponse(json.dumps(result))
    form_obj = LoginForm()
    return render(request, "login2.html", {"form_obj": form_obj})

# 登录
class Login(View):
    def get(self, request):
        form_obj = LoginForm()
        return render(request,"login.html",{"form_obj": form_obj})

    def post(self, request):
        res = {"code": 0}
        print(request.POST)
        username = request.POST.get("username")
        pwd = request.POST.get("password")
        v_code = request.POST.get('v_code')
        print(v_code)
        # 先判断验证码是否正确
        if v_code.upper() != request.session.get("v_code", ""):
            res["code"] = 1
            res["msg"] = "验证码错误"
        else:
            # 进行校验用户名密码是否正确
            user = authenticate(username=username,password=pwd)
            if user:
                # 用户名密码正确
                login(request,user)
            else:
                # 用户名或密码错误
                res["code"] = 1
                res["msg"] = "用户名或密码错误"
        return JsonResponse(res)


# 首页
class Index(View):
    def get(self, request):
        article_list = models.Article.objects.all()
        data_amount = article_list.count()  # 获取总共多少片文章
        page_num = request.GET.get("page",1)  # 获取第一页
        page_obj = MyPage(page_num,data_amount,per_page_data=1,url_prefix='index')
        page_html = page_obj.ret_html()    # 获取当前左右数据
        data = article_list[page_obj.start:page_obj.end]  # 起始页码
        return render(request,"index.html",{"article_list": data, "page_html":page_html})


# 专门用来返回验证码图片的视图
@never_cache
def v_code(request):
    # 随机生成图片
    # 生成随机颜色的方法
    def random_color():
        return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    # 生成图片对象
    image_obj = Image.new(
        "RGB",  # 生成图片的模式
        (250, 35),  # 图片大小
        random_color()
    )
    # 生成一个准备写字的画笔
    draw_obj = ImageDraw.Draw(image_obj)   # image_obj是在那里写
    font_obj = ImageFont.truetype('static/font/kumo.ttf', size=28)  # 加载本地的字体文件
    # 生成随机验证码，五位的，字母和数字
    tmp = []
    for i in range(5):
        n = str(random.randint(0, 9))
        l = chr(random.randint(65, 90))
        u = chr(random.randint(97, 122))
        r = random.choice([n, l, u])
        tmp.append(r)
        # 每一次取到要写的东西之后，往图片上写
        draw_obj.text(
            (i*45+25, 0),  # 坐标
            r,  # 内容
            fill=random_color(),  # 颜色
            font=font_obj  # 字体
        )
    v_code = "".join(tmp)  # 得到最终的验证码
    request.session['v_code'] = v_code.upper()

    # 直接将生成的图片保存在内存中
    f = BytesIO()
    image_obj.save(f, "png")
    # 从内存读取图片数据
    data = f.getvalue()
    return HttpResponse(data,content_type="image/png")


# 注册 用局部钩子判断用户是否注册
class RegView(View):
    def get(self, request):
        form_obj = RegisterForm()
        return render(request, "register.html", {"form_obj": form_obj})

    def post(self, request):
        res = {"code": 0}
        print(request.POST)
        # 然后进行校验验证码
        v_code = request.POST.get("v_code", "")
        if v_code.upper() == request.session.get("v_code", ""):
            # 验证码正确,开始获取注册的数据，
            form_obj = RegisterForm(request.POST)
            # 使用form做校验，这个时候要使用钩子函数，对两个密码进行校验
            if form_obj.is_valid():
                # 数据有效的话，继续往下进行,又因为，获取的数据中有re密码，数据库中不需要这个东西，所以要移除
                form_obj.cleaned_data.pop("re_password")
                # 拿到用户上传的头像文件
                avatar_file = request.FILES.get('avatar')
                # 这个时候就可以写入数据库中了,注意要打散
                models.UserInfo.objects.create_user(**form_obj.cleaned_data, avatar=avatar_file)
                # 登录成功之后就可以跳转到登录页面即可
                res["msg"] = "/login/"
            # 以上是正常进行是正确的，但是难免会有用户乱填，这样就要有报错信息了
            else:
                res["code"] = 1
                res["msg"] = form_obj.errors  # 获取错误信息
        else:
            res["code"] = 2
            res["msg"] = "验证码错误"
        return JsonResponse(res)


# 注销
def logout1(request):
    auth.logout(request)
    return redirect('/login/')


# 个人博客，我没写就是每个人的背景，只单独写了一个背景
def every(request,username):
    print(request.user)
    # 先找到这个当前用户
    # user_obj = models.UserInfo.objects.filter(username=username).first()
    user_obj = get_object_or_404(models.UserInfo, username=username)    # 找不到的话就是报404错误
    # 查找当前用户关联的blog对象
    blog = user_obj.blog
    aticle_listr = models.Article.objects.filter(user=user_obj)
    tag_list = models.Tag.objects.filter(blog=blog)
    cart_list = models.Category.objects.filter(blog=blog)
    article_list = models.Article.objects.filter(user__username=request.user)
    # tag_list = models.Tag.objects.filter(blog=request.user.blog)
    # cart_list =models.Category.objects.filter(blog=request.user.blog)
    # date_list = models.Article.objects.all()
    # return render(request,'erery.html',{'article_list':article_list,"tag_list": tag_list,"cart_list":cart_list,"date_list":date_list})
    return render(request,'erery.html',{'article_list':article_list,"tag_list": tag_list,"cart_list":cart_list,"user_obj":user_obj})


# 个人博客，每个人有自己的背景，并且有自己的样式
# def home(request, username, *args):
#     # user_obj = models.UserInfo.objects.filter(username=username).first()
#     user_obj = get_object_or_404(models.UserInfo, username=username)  # 找不到的话就是报404错误
#     # 然后查找到这个用户用到的博客站点
#     blog = user_obj.blog
#     tag_list = models.Tag.objects.filter(blog=blog)
#     cart_list = models.Category.objects.filter(blog=blog)
#     # 日期归档
#    对当前blog的所有文章按照年月 分组 查询
    # 1. models.Article.objects.filter(user=user_obj)                   --> 查询出当前作者写的所有文章
    # 2. .extra(select={"y_m": "DATE_FORMAT(create_time, '%%Y-%%m')"}   --> 将所有文章的创建时间格式化成年-月的格式，方便后续分组
    # 3. .values("y_m").annotate(c=Count("id"))                         --> 用上一步时间格式化得到的y_m字段做分组，统计出每个分组对应的文章数
    # 4. .values("y_m", "c")                                            --> 把页面需要的日期归档和文章数字段取出来
#     archive_list = models.Article.objects.filter(user=user_obj).extra(
#         select={"y_m": "DATE_FORMAT(create_time, '%%Y-%%m')"}
#     ).values("y_m").annotate(c=Count("id")).values("y_m", "c")
#     article_list = models.Article.objects.filter(user=user_obj)
#     print(args)
#     if args:
#         if args[0] == "tag":
#             # 表示按照文章的标签查询
#             article_list = article_list.filter(tags__title=args[1])
#         elif args[0] == "category":
#             # 表示按照文章的分类查询
#             article_list = article_list.filter(category__title=args[1])
#         else:
#             try:
#             # 表示按照文章的日期归档查询
#                 year, month = args[1].spilt("-")
#                 article_list = article_list.filter(create_time__year=year,create_time__month=month)
#             except Exception as e:
#                 article_list = []
#     return render(
#         request,'home.html',
#         {'article_list':article_list,
#          "tag_list": tag_list,
#          "cart_list":cart_list,
#          "user":user_obj,
#          "archive_list":archive_list,
#          "blog":blog
#          }
#     )
def home(request, username, *args):
    user_obj = get_object_or_404(models.UserInfo, username=username)
    blog = user_obj.blog
    article_list = models.Article.objects.filter(user=user_obj)
    if args:
        if args[0] == "category":
            article_list = article_list.filter(category__title=args[1])
        elif args[0] == "tag":
            article_list = article_list.filter(tags__title=args[1])
        else:
            try:
                year, month = args[1].split("-")
                article_list = article_list.filter(create_time__year=year, create_time__month=month)
            except Exception as e:
                article_list = []

    return render(request, "home.html", {
        "blog": blog,
        "username": username,
        "article_list": article_list
    })


# 左边菜单栏获取到的数据
# def left_menu(username):
#     user_obj = models.UserInfo.objects.filter(username=username).first()
#
#     # 查找当前用户关联的blog对象
#     blog = user_obj.blog
#     # 查找当前blog对应的文章分类有哪些
#     category_list = models.Category.objects.filter(blog=blog)
#     # 查找当前blog对应的文章标签有哪些
#     tag_list = models.Tag.objects.filter(blog=blog)
#     # 对当前blog的所有文章按照年月 分组 查询
#     # 1. models.Article.objects.filter(user=user_obj)                   --> 查询出当前作者写的所有文章
#     # 2. .extra(select={"y_m": "DATE_FORMAT(create_time, '%%Y-%%m')"}   --> 将所有文章的创建时间格式化成年-月的格式，方便后续分组
#     # 3. .values("y_m").annotate(c=Count("id"))                         --> 用上一步时间格式化得到的y_m字段做分组，统计出每个分组对应的文章数
#     # 4. .values("y_m", "c")                                            --> 把页面需要的日期归档和文章数字段取出来
#     archive_list = models.Article.objects.filter(user=user_obj).extra(
#         select={"y_m": "DATE_FORMAT(create_time, '%%Y-%%m')"}
#     ).values("y_m").annotate(c=Count("id")).values("y_m", "c")
#
#     return user_obj, blog, category_list, tag_list, archive_list

# 个人详情
def article(request, username, id):
    user_obj = get_object_or_404(models.UserInfo, username=username)
    blog = user_obj.blog
    article_obj = models.Article.objects.filter(id=id).first()
    # 找到当前文章的评论
    comment_list = models.Comment.objects.filter(article=article_obj)
    return render(request, 'article.html',
                  {
                      "blog": blog,
                      "article": article_obj,
                      "username": username,
                      "comment_list":comment_list,
                  })


# 点赞
def updown(request):
    if request.method == "POST":
        res = {"code": 0}
        print(request.POST)
        print(request.user.username)
        user_id = request.POST.get("userId")
        article_id = request.POST.get("articleId")
        is_up = request.POST.get("isUp")
        # print(is_up, type(is_up))
        is_up = True if is_up.upper() == 'TRUE' else False
        # 5.不能给自己点赞
        article_obj = models.Article.objects.filter(id=article_id, user_id=user_id)
        if article_obj:
            # 表示是给自己写的文章点赞
            res["code"] = 1
            res["msg"] = '不能给自己的文章点赞！' if is_up else '不能反对自己的内容！'
        # 3.同一个人只能给同一篇文章点赞一次
        # 4.点赞和反对两个只能选一个
        # 判断一下当前这个人和这篇文章 在点赞表里有没有记录
        else:
            is_exist = models.ArticleUpDown.objects.filter(user_id=user_id, article_id=article_id).first()
            if is_exist:
                res["code"] = 1
                res["msg"] = '已经点过赞' if is_exist.is_up else '已经反对过'
            else:
                # 真正点赞
                # 注意？
                # 事务操作，，
                with transaction.atomic():
                    # 1. 先创建点赞记录
                    models.ArticleUpDown.objects.create(user_id=user_id, article_id=article_id, is_up=is_up)
                    # 2. 再更新文章表
                    if is_up:
                        # 更新点赞数
                        models.Article.objects.filter(id=article_id).update(up_count=F('up_count')+1)
                    else:
                        # 更新反对数
                        models.Article.objects.filter(id=article_id).update(down_count=F('down_count') + 1)
                res["msg"] = '点赞成功' if is_up else '反对成功'
        return JsonResponse(res)


# 评论
def comment(request):
    if request.method == "POST":
        res = {"code": 0}
        article_id = request.POST.get("article_id")
        content = request.POST.get("content")
        user_id = request.user.id
        parent_id = request.POST.get("parent_id")

        with transaction.atomic():
            if parent_id:
                # 添加子评论,字段包括用户名，还有这个文章，还有这个父级ID，还有内容
                comment_obj = models.Comment.objects.create(content=content,article_id=article_id,user_id=user_id,parent_comment_id=parent_id)
            else:
                # 添加父评论
                comment_obj = models.Comment.objects.create(content=content,article_id=article_id,user_id=user_id)
        # 2. 去更新该文章的评论数
        models.Article.objects.filter(id=article_id).update(comment_count=F("comment_count")+1)
        res["data"] = {
            "id": comment_obj.id,
            "content":comment_obj.content,
            "create_time":comment_obj.create_time.strftime("%Y-%m-%d %H-%M"),
            "username":comment_obj.user.username
        }
    return JsonResponse(res)


# 博客管理后台
def backend(request):
    # 获取这个当前用户的所有文章
    article_list = models.Article.objects.filter(user=request.user)
    return render(request, "backend.html", {"article_list": article_list})


# 增加新文章
def add_article(request):
    if request.method == "POST":
        # 获取文章的内容
        title = request.POST.get("title")
        content = request.POST.get("content")
        category_id = request.POST.get("category")
        tag_id = request.POST.get("tag")
        # 清洗用户发布的文章的内容，去掉script标签
        soup = BeautifulSoup(content, "html.parser")  # 对一段HTML格式的内容做解析
        script_list = soup.select("script")
        for i in script_list:
            i.decompose()     # 删除标签,
        # 存入数据库,创建文章记录和创建文章详情记录是同步的，所以用到事务
        with transaction.atomic():
            # 创建文章记录
            article_obj = models.Article.objects.create(
                title=title,
                desc=soup.text[0:200],   # 取text文本内容
                user=request.user,
                category_id=category_id
            )
            # 创建文章详情记录
            models.ArticleDetail.objects.create(
                content=soup.prettify(),  # 格式化html内容
                article=article_obj
            )
        return redirect("/blog/backend/")
    # 把当前博客的文章分类查询出来
    category_list = models.Category.objects.filter(blog__userinfo=request.user)
    # 跨了两张表，文章分类联系博客站点，然后博客站点和用户信息是一对一，是查出来的是一个对象
    tag_list = models.Tag.objects.filter(blog__userinfo=request.user)
    return render(request,"add_article.html", {"category_list": category_list, "tag_list": tag_list})


# 富文本的图片处理
def upload(request):
    res = {"error": 0}
    print(request.FILES)  # <MultiValueDict: {'imgFile': [<InMemoryUploadedFile: 6-141105212625A8.jpg (image/jpeg)>]}>
    file_obj = request.FILES.get("imgFile")  # 获取到文件名
    file_path = os.path.join(settings.MEDIA_ROOT, "article_imgs", file_obj.name)
    with open(file_path, "wb") as f:
        for chunk in file_obj.chunks():
            f.write(chunk)
    # 拼路由
    url = "/media/article_imgs/" + file_obj.name
    res["url"] = url
    return JsonResponse(res)

