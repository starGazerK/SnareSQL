import time
import hashlib
from itertools import chain
import random,urllib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.shortcuts import render
from django.utils import timezone
from django.utils.safestring import mark_safe
from flask import *
from common.mysqllib import gmysql
import urllib.parse
def insert_adm(nr): #type,ip,url,info
    myd=gmysql('adm.db')
    ds=time.strftime('%Y-%m-%d %H:%M:%S')
    #             rr = ['SQL', ip, url, ss]  # 将相关信息组成一个列表
    sql=r"insert into log(put_time,type,ip,url,info) values ('%s','%s','%s','%s','%s');"
    # nr[3]=urllib.parse.quote(nr[3])
    sql=sql%(ds,nr[0],nr[1],nr[2],nr[3].replace("'", "''"))
    ret=myd.put_data(sql)


def my_model_to_dict(instance, fields=None, exclude=None, has_editable=True):
    """
        model to dict。

        Args:
            instance: model
            fields: プロパティを指定する
            exclude: プロパティを除外する
            has_editable: 自動更新も含めて処理する
        return:
            dict
    """
    opts = instance._meta
    
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if not has_editable and not getattr(f, "editable", False):
            # 若不处理自己动更新字段，则跳过
            continue
        if fields is not None and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)
    return data

def model_to_d(dat,exf=[]):
    res=[]
    for d in dat:            
        dt=my_model_to_dict(d)
        for f in exf:
            dt[f]=eval('d.'+f)
        res.append(dt)

    return res
    
def okmsg(msg='ok',close=False,fwr=''):  #  组成成功信息
    if close:
        res={"message":msg,"statusCode":200,"navTabId":"","callbackType":'closeCurrent',"forwardUrl":fwr}                
    else:
        res={"message":msg,"statusCode":200,"navTabId":"","callbackType":'',"forwardUrl":fwr}                
    return res;

def failmsg(msg='fail'):   #  组成失败信息
    res={"message":msg,"statusCode":300,"navTabId":"","callbackType":'closeCurrent'}                
    return res

def viewImage(obj , src):
    return mark_safe('<img src="%s" style="width:50px" />'%(  src , ))

def viewImages(obj , src):
    return mark_safe('<img src="%s" style="width:50px" />'%(  src , ))

def getID():
    itme_id = str(int(time.time() * 1000)) + str(int(time.perf_counter() / 1000))
    return itme_id

def getDate():
    d1 = timezone.now()
    return d1

def getDateStr():
    d1 = timezone.now()
    return d1.strftime("%Y-%m-%d")

def getTimeStr():
    d1 = timezone.now()
    return d1.strftime("%H:%M:%S")
def getDaytimestr():
    d1 = timezone.now()
    rds=str(random.randint(100,999))
    res=d1.strftime("%Y%m%d-%H%M%S")+rds
    return res

def getDateTimeStr():
    d1 = timezone.now()
    return d1.strftime("%Y-%m-%d %H:%M:%S")


def input(request , name , default = None):
    if name in request.args:
        return request.args.get(name , default)
    if name in request.form:
        return request.form.get(name , default)
    return default

def inputlist(request , name , default = None):
    if name in request.GET:
        return request.GET.getlist(name , default)
    if name in request.POST:
        return request.POST.getlist(name , default)
    return default

def session(request , name):
    if name in request.session:
        return request.session[name]
    return ""

def checkLogin(request):
    if "username" in request.session:
        return True
    return False

def showMessage(request , message , code = 0 , href = 'javascript:history.go(-1);' , icon = None , auto_redirect = True , auto_time = 3):
    content = {
        'data': message,
        'code': code,
        'msg':message,
        'href': href,
        'icon': icon,
        'auto_redirect': auto_redirect,
        'auto_time': auto_time
    }
    if icon is None:
        if code > 0:
            content['icon'] = 'error'
        else:
            content['icon'] = 'success'

    return render(request , 'message.html' , content)

def showSuccess(request , message , href = None, icon = None , auto_redirect = True):
    if href is None:
        href = request.headers['referer']
    return showMessage(request , message,0,href , icon=icon,auto_redirect=auto_redirect)



def showError(request , message , href = 'javascript:history.go(-1);', icon = None , auto_redirect = True):
    return showMessage(request, message, 1, href , icon = icon , auto_redirect=auto_redirect)


def md5(str):
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    print(m.hexdigest())
    return m.hexdigest()


def parseName(name):
    result = ''
    isUpper = False
    for index,name_char in enumerate(name):
        if index == 0:
            result += str(name_char).upper()
        elif str(name_char) == '_':
            isUpper = True
        else:
            if isUpper:
                result += str(name_char).upper()
            else:
                result += str(name_char)

    return result


class LazyImport(object):
    """
    动态导入模块
    """
    def __init__(self, module_name, module_class):
        """
        :param module_name:
        :param module_class:
        :return: 等同于 form module_name import module_class
        """
        self.module_name = module_name
        self.module_class = module_class
        self.module = None

    def __getattr__(self, name):
        if self.module is None:
            self.module = __import__(self.module_name, fromlist=[self.module_class])
        return getattr(self.module, name)

def imports(filename, clsname):
    importmodule = LazyImport(filename, clsname)  # 导入classname模块
    is_true = hasattr(importmodule, clsname)  # 检查classname类是否在classname模块中
    if is_true:
        classname = getattr(importmodule, clsname)
        return classname
    return None



_letter_cases = "123456789"  # 小写字母，去除可能干扰的i，l，o，z
_upper_cases = _letter_cases.upper()  # 大写字母
_numbers = ''.join(map(str, range(3, 10)))  # 数字
init_chars = ''.join((_letter_cases, _upper_cases, _numbers))

# 创建验证码
def create_validate_code(size=(120, 30),
                         chars=init_chars,
                         img_type="PNG",
                         mode="RGB",
                         bg_color=(255, 255, 255),
                         fg_color=(0, 0, 255),
                         font_size=18,
                         font_type="arial.ttf",
                         length=4,
                         draw_lines=True,
                         n_line=(1, 2),
                         draw_points=True,
                         point_chance=2):
    """
    @todo: 生成验证码图片
    @param size: 图片的大小，格式（宽，高），默认为(120, 30)
    @param chars: 允许的字符集合，格式字符串
    @param img_type: 图片保存的格式，默认为GIF，可选的为GIF，JPEG，TIFF，PNG
    @param mode: 图片模式，默认为RGB
    @param bg_color: 背景颜色，默认为白色
    @param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
    @param font_size: 验证码字体大小
    @param font_type: 验证码字体，默认为 arial.ttf
    @param length: 验证码字符个数
    @param draw_lines: 是否划干扰线
    @param n_lines: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
    @param draw_points: 是否画干扰点
    @param point_chance: 干扰点出现的概率，大小范围[0, 100]
    @return: [0]: PIL Image实例
    @return: [1]: 验证码图片中的字符串
    """

    width, height = size  # 宽高
    # 创建图形
    img = Image.new(mode, size, bg_color)
    draw = ImageDraw.Draw(img)  # 创建画笔

    def get_chars():
        """生成给定长度的字符串，返回列表格式"""
        return random.sample(chars, length)

    def create_lines():
        """绘制干扰线"""
        line_num = random.randint(*n_line)  # 干扰线条数

        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            # 结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))

    def create_points():
        """绘制干扰点"""
        chance = min(100, max(0, int(point_chance)))  # 大小限制在[0, 100]

        for w in range(width):
            for h in range(height):
                tmp = random.randint(0, 100)
                if tmp > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    def create_strs():
        """绘制验证码字符"""
        c_chars = get_chars()
        strs = ' %s ' % ' '.join(c_chars)  # 每个字符前后以空格隔开

        font = ImageFont.truetype(font_type, font_size)
        font_width, font_height = font.getsize(strs)

        draw.text(((width - font_width) / 3, (height - font_height) / 3),
                  strs, font=font, fill=fg_color)

        return ''.join(c_chars)

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    strs = create_strs()

    # 图形扭曲参数
    params = [1 - float(random.randint(1, 2)) / 100,
              0,
              0,
              0,
              1 - float(random.randint(1, 10)) / 100,
              float(random.randint(1, 2)) / 500,
              0.001,
              float(random.randint(1, 2)) / 500
              ]
    #img = img.transform(size, Image.PERSPECTIVE, params)  # 创建扭曲
    #img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 滤镜，边界加强（阈值更大）
    return img, strs


#import decimal
#import json
#class DecimalEncoder(json.JSONEncoder):
#    def default(self, o):
#        if isinstance(o, decimal.Decimal):
#            return float(o)
#        super(DecimalEncoder, self).default(o)


import decimal
import json
import datetime
from django.core.serializers.json import DjangoJSONEncoder
class DecimalEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o , datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        super(DecimalEncoder, self).default(o)
