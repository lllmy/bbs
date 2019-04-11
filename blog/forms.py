from django import forms
from blog import models
from django.core.validators import RegexValidator  # 正则表达式
from django.core.exceptions import ValidationError  # 全局钩子函数的时候抛出异常用到的
# form组件登录
class LoginForm(forms.Form):
    username = forms.CharField(
        label="用户名",
        min_length=4,
        error_messages={
            "required" : "用户名不能为空",
            "min_length": "用户名不能少于4位"
        },
        widget=forms.widgets.TextInput(
            attrs={"class": "form-control"}
        )
    )
    password = forms.CharField(
        label="密码",
        min_length=6,
        error_messages={
            "required": "密码不能为空",
            "min_length": "密码不能少于4位"
        },
        widget=forms.widgets.PasswordInput(
            attrs={"class": "form-control"}
        )
    )


# form注册
class RegisterForm(forms.Form):
    username = forms.CharField(
        label="用户名",
        min_length=4,
        error_messages={
            "required": "用户名不能为空",
            "min_length":"用户名不能少于4位"
        },
        widget=forms.widgets.TextInput(
            attrs={"class": "form-control"}
        )
    )
    password = forms.CharField(
        label="密码",
        min_length=6,
        error_messages={
            "required": "密码不能为空",
            "min_length": "密码不能少于6位"
        },
        widget=forms.widgets.PasswordInput(
            attrs={"class": "form-control"}
        )
    )
    re_password = forms.CharField(
        label="确认密码",
        min_length=6,
        error_messages={
            "required": "密码不能为空",
            "min_length": "密码不能少于6位"
        },
        widget=forms.widgets.PasswordInput(
            attrs={"class": "form-control"}
        )
    )
    phone = forms.CharField(
        label="手机号",
        error_messages={
            "required": "手机号不能为空",
        },
        validators=[RegexValidator(r'1[3-9]\d{9}',"手机号格式不正确")],
        widget=forms.widgets.TextInput(
            attrs={"class": "form-control"}
        )
    )
    email = forms.CharField(
        label='邮箱',
        error_messages={
            "required": "邮箱不能为空",
        },
        validators=[RegexValidator(r'^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$', "邮箱格式不正确")],
        widget=forms.widgets.EmailInput(
            attrs={"class": "form-control"}
        )
    )


# 局部钩子函数，用于判断用户名是否存在
    def clean_username(self):
        # 取到用户名
        username = self.cleaned_data.get("username")
        # 与数据库中比较
        is_exist = models.UserInfo.objects.filter(username=username)
        if is_exist:
            # 表示如果用户名已存在，说明该用户名已经注册
            raise ValidationError("该用户已被注册")
        else:
            return username


# 全局钩子函数
    def clean(self):
        pwd = self.cleaned_data.get("password")
        re_pwd = self.cleaned_data.get("re_password")
        if re_pwd and re_pwd == pwd:
            return self.cleaned_data
        else:
            self.add_error("re_password", "两次密码不一致")
            raise ValidationError("两次密码不一致")