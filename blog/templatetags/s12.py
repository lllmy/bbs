from django import template
from blog import models
from django.db.models import Count
# 实例必须叫这个名字
register = template.Library()


@register.inclusion_tag(filename="left-menu.html")
def left_menu(username):
    user_obj = models.UserInfo.objects.filter(username=username).first()

    # 查找当前用户关联的blog对象
    blog = user_obj.blog
    # 查找当前blog对应的文章分类有哪些
    category_list = models.Category.objects.filter(blog=blog)
    # 查找当前blog对应的文章标签有哪些
    tag_list = models.Tag.objects.filter(blog=blog)
    # 对当前blog的所有文章按照年月 分组 查询
    # 1. models.Article.objects.filter(user=user_obj)                   --> 查询出当前作者写的所有文章
    # 2. .extra(select={"y_m": "DATE_FORMAT(create_time, '%%Y-%%m')"}   --> 将所有文章的创建时间格式化成年-月的格式，方便后续分组
    # 3. .values("y_m").annotate(c=Count("id"))                         --> 用上一步时间格式化得到的y_m字段做分组，统计出每个分组对应的文章数
    # 4. .values("y_m", "c")                                            --> 把页面需要的日期归档和文章数字段取出来
    archive_list = models.Article.objects.filter(user=user_obj).extra(
        select={"y_m": "DATE_FORMAT(create_time, '%%Y-%%m')"}
    ).values("y_m").annotate(c=Count("id")).values("y_m", "c")

    return {
        "username": username,
        "category_list": category_list,
        "tag_list": tag_list,
        "archive_list": archive_list
    }