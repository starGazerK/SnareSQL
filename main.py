import datetime
import sqlite3

from flask import *
from common import utils
from common.mysqllib import gmysql
from os import urandom
import os, time, re
from adm_view import *
import honeypot
from multiprocessing import Pool
from urllib.parse import unquote

app = Flask(__name__)  # 实例化并命名为app实例
app.config['SESSION_TYPE'] = 'filesystem'  # 设置会话存储方式
app.config['SESSION_FILE_DIR'] = 'D:\fk_web'  # 设置会话文件的存储位置
app.secret_key = urandom(50)  # 设置密钥加密会话数据，随机字符串
# 设置上传文件的保存目录
UPLOAD_FOLDER = './static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Session(app)

def mylog(nr):  # 日志子函数    
    print(nr)
    ss = time.strftime('%Y-%m-%d %H:%M:%S,')  # 获取当前的日期和时间,并将其格式化为'YYYY-MM-DD HH:MM:SS,'的形式
    with open('run.log', 'a') as f:  # 以追加模式打开名为 run.log 的文件,并将文件对象赋值给变量 f
        f.write(ss + nr + '\n')  # 将时间戳 ss、输入的字符串nr以及一个换行符\n拼接起来,写入到 run.log 文件


def post_sql_chk(request):  # post和GET 请求检查. 本函数检查所有来自HTML前端的请求参数，分析是否有SQL注入关键词
    if request.method == 'POST':
        data = request.form  # 取所有请求参数
    # 从 Flask 的 request 对象中获取所有通过表单提交的请求参数,并将它们存储在 data 变量中
    elif request.method == 'GET':
        data = request.args  # 从 Flask 的 request 对象中获取所有通过 URL 查询参数提交的请求参数,并将它们存储在 data 变量中。

    for v in data:  # 循环遍历所有通过 GET 或 POST 请求传递的每个参数
        # 正则表达式定义了一个模式,用于匹配常见的 SQL 注入关键词和符号，检查每个参数是否包含注入关键字
        pattern = r"\b(or|and|like|exec|insert|select|drop|grant|alter|chr|mid|master|truncate|char|delclare|'|\"|;|\*)"
        if request.method == 'POST':
            nr = request.form[v]  # 检索当前参数的值
        else:
            nr = request.args[v]
        nr = str(nr).lower()  # 将参数值全部变小写，以便进行不区分大小写的匹配
        r = re.search(pattern, nr)  # 使用正则表达式检测请求参数字串是否有sql关键词，扫描整个字符串，返回第一个成功的匹配
        if r:  # 如果找到则可疑的SQL注入关键词
            url = request.path  # 取攻击者使用的url
            ip = request.remote_addr  # 取攻击者ip 
            ds = str(data).replace('ImmutableMultiDict', '')  # 将请求参数转换为字符串
            ss = '可疑的%s,参数:%s 内容:%s' % (request.method, v, nr)  # 构建一条日志信息
            rr = ['SQL', ip, url, ss]  # 将相关信息组成一个列表
            utils.insert_adm(rr)  # type,ip,url,info
            # 调用 utils 模块的 insert_adm 函数将信息写入数据库。
            mylog('%s,%s,%s' % (ip, url, ds))  # 调用 mylog 函数将信息写入日志文件
            return True  # 返回 True，表示检测到可疑的 SQL 注入
    return False


@app.before_request  # 全局拦截器 用于在应用程序的路由处理所有传入请求之前拦截和处理这些请求，进行分析是否有注入行为
def process_request():  # 每次请求之前将执行的函数
    if request.path == "/login" and request.method == 'POST':  # 检查传入请求是否是对“/login”URL的POST请求（从登录页面传来的请求）
        post_sql_chk(request)  # 由于登录页面有SQL注入点，故调用post_sql_chk（request）函数来检查潜在的 SQL 注入攻击
    if request.path == "/user/list/" and request.method == 'GET':
        post_sql_chk(request)
    if request.path == "/get_all_contract/":
        post_sql_chk(request)
    if request.path == "/get_eventlist/":
        post_sql_chk(request)
    if request.path[:8] == '/static/':  # 如果url是要读取静态文件，直接放行
        return None
    if request.path in ["/login", "/8ad9min0124", '/logout', '/front_index', '/index','/']:  # 如果传入的请求是针对登录、管理界面、登出的，也放行
        return None
    if not session.get("user_id"):  # 通过检查会话中是否存在“user_id”键来检查用户是否已登录
        return redirect("/login")  # 如果用户未登录，则会将其重定向到登录页面
    return None


# 合同数据管理

@app.route('/user/list/', methods=["GET", "POST"])  # 路由－－对应执行的函数
def getdata():
    wdo = utils.input(request, 'do', '')
    ids = utils.input(request, 'id', '')
    page = utils.input(request, 'page', '')
    limit = utils.input(request, 'limit', '')
    if wdo == '':  # 什么子操作都没有 则加载list.html显示表格
        act = '/user/list/'
        return render_template("list.html", act=act)
        # return render_template("user/user-table.html", act=act)
    elif wdo == 'getdata':  # 前端HTML页面通过JS，向后台申请数据
        nms = utils.input(request, 'name', '')  # 取前端回传的 name 参数
        # 确保page和limit都是整数
        '''page = int(page) if page.isdigit() else 1
        limit = int(limit) if limit.isdigit() else 10
        offset = (page - 1) * limit  # 计算偏移量'''
        myd = gmysql('db.sqlite3')  # 打开数据库
        # 基本的SQL查询
        sql = r"SELECT id, name, manager, contractor, buy_fm FROM data"
        # count_sql = "SELECT COUNT(*) FROM data"  # 用于计算总数的SQL

        if nms:  # 如果查询 name字段
            sql+=f' where name like \'%%{nms}%%\''
            #sql += f" WHERE name LIKE '%%{nms}%%'"  # 增加查询SQL内容
            #count_sql += f" WHERE name LIKE '%%{nms}%%'"  # 同步修改计数SQL
        # print(f"nms:{nms}")
        # sql += f" LIMIT {limit} OFFSET {offset}"  # 添加LIMIT和OFFSET用于分页

        data = myd.get_data(sql, 1)  # 取数据
        '''total_count = myd.get_data(count_sql, 0)  # 获取总记录数，返回形式如 (5,)
        if total_count is not None:
            total_count = total_count[0]  # 提取总记录数
        else:
            total_count = 0  # 如果无法获取，设为0'''
        dat = []
        for d in data:  # 将数据行变成JSON列表。
            t = {'id': d[0], 'name': d[1], 'manager': d[2], 'contractor': d[3],'buy': d[4]}
            dat.append(t)
        resp_data = {
            'code': 0,
            'msg': "success",
            #'count': total_count,  # 返回总记录数
            'data': dat
        }
        return jsonify(resp_data)  # 发回前端显示
        #return jsonify(dat)
    elif wdo == 'delrow':  # 删除记录
        print("删除")
        myd = gmysql('db.sqlite3')
        sql = r"delete from data where id=" + ids
        try:
            myd.put_data(sql)
            ret = utils.okmsg('成功删除')
        except Exception as e:
            ret = utils.failmsg('删除出错 ：' + str(e))
        return jsonify(ret)
    elif wdo == 'openmod_e':  # 修改或增加记录
        if ids == '':  # 打开增加记录窗口
            act = '/user/list/?do=new'
            dat = {'id': ''}  # ,'name':d[1],'date':d[2],'manager':d[3],'buy':d[4]}
        else:  # 打开修改记录窗口
            myd = gmysql('db.sqlite3')
            sql = r"select * from data where id=" + ids
            d = myd.get_data(sql)  # 读取要修改的记录
            act = '/user/list/?do=update'
            #dat = {'id': d[0], 'name': d[1], 'manager': d[2], 'Sign_date': d[3], 'Paydate': d[4], 'contractor': d[5],
            #       'buy_fm': d[6]}
            dat = {'id': d[0], 'name': d[1], 'manager': d[2], 'contractor': d[3], 'buy': d[4]}  # 变成json数据，
        return render_template("mod_nr.html", act=act, dat=dat)  # 显示修改页面，同时加载json数据
    elif wdo == 'new':  # 插入记录
        name = utils.input(request, 'name', '')  # 取前端参数
        manager = utils.input(request, 'manager', '')
        sign_date = utils.input(request, 'Sign_date', '')
        paydate = utils.input(request, 'Paydate', '')
        contractor = utils.input(request, 'contractor', '')
        buy_fm = utils.input(request, 'buy_fm', '')
        if buy_fm == '':
            buy_fm = '暂无记录'
        sql = f"insert into data(name,Sign_date,Paydate,contractor,manager,buy_fm) values('{name}','{sign_date}','{paydate}','{contractor}','{manager}','{buy_fm}')"
        myd = gmysql('db.sqlite3')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    elif wdo == 'update':  # 修改记录
        name = utils.input(request, 'name', '')  # 取前端参数
        manager = utils.input(request, 'manager', '')
        sign_date = utils.input(request, 'Sign_date', '')
        paydate = utils.input(request, 'Paydate', '')
        contractor = utils.input(request, 'contractor', '')
        buy_fm = utils.input(request, 'buy_fm', '')
        sql = f"update  data set name='{name}',paydate='{paydate}',contractor='{contractor}',Sign_date='{sign_date}',manager='{manager}',buy_fm='{buy_fm}' where id={ids}"
        print(f"get_data: {sql}")
        myd = gmysql('db.sqlite3')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    else:
        act = '/user/list/'  # 定义 act 变量，确保在所有使用场景下都已定义
        return render_template("list.html", act=act)


'''@app.route('/news', methods=['GET', 'POST'])
def get_news():
    myd = gmysql('db.sqlite3')  # 打开数据库
    sql = r"select id,title,content,notice_url,create_time from news"  # SQL命令
    data = myd.get_data(sql, 1)  # 取数据
    dat = []
    for d in data:  # 将数据行变成JSON列表。
        t = {'id': d[0], 'name': d[1], 'manager': d[2], 'Sign_date': d[3], 'Paydate': d[4], 'contractor': d[5],
             'buy': d[6]}
        dat.append(t)
    return jsonify(dat)  # 发回前端显示'''


# 合同下载
@app.route('/get_all_contract/', methods=["GET", "POST"])
def get_all_contract():
    wdo = utils.input(request, 'do', '')
    ids = utils.input(request, 'id', '')
    page = utils.input(request, 'page', '')
    limit = utils.input(request, 'limit', '')
    if wdo == '':  # 什么子操作都没有 则加载list.html显示表格
        act = '/get_all_contract/'
        return render_template("get_all_contract.html", act=act)
    elif wdo == 'getdata':  # 前端HTML页面通过JS，向后台申请数据
        nms = utils.input(request, 'contract_name', '')  # 取前端回传的 name 参数
        page = int(page) if page.isdigit() else 1
        limit = int(limit) if limit.isdigit() else 10
        offset = (page - 1) * limit  # 计算偏移量
        myd = gmysql('db.sqlite3')  # 打开数据库
        sql = r"select id,contract_name,type from contract_list"  # SQL命令
        count_sql = "SELECT COUNT(*) FROM contract_list"  # 用于计算总数的SQL
        if nms:  # 如果查询 name字段
            sql += f" WHERE contract_name LIKE '%%{nms}%%'"  # 增加查询SQL内容
            count_sql += f" WHERE contract_name LIKE '%%{nms}%%'"  # 同步修改计数SQL
        print(f"nms:{nms}")
        sql += f" LIMIT {limit} OFFSET {offset}"  # 添加LIMIT和OFFSET用于分页

        data = myd.get_data(sql, 1)  # 取数据
        total_count = myd.get_data(count_sql, 0)  # 获取总记录数，返回形式如 (5,)
        if total_count is not None:
            total_count = total_count[0]  # 提取总记录数
        else:
            total_count = 0  # 如果无法获取，设为0
        dat = []
        for d in data:  # 将数据行变成JSON列表。
            t = {'id': d[0], 'contract_name': d[1], 'type': d[2]}
            dat.append(t)
        resp_data = {
            'code': 0,
            'msg': "success",
            'count': total_count,  # 返回总记录数
            'data': dat
        }
        return jsonify(resp_data)  # 发回前端显示
    elif wdo == 'delrow':  # 删除记录
        print("删除")
        myd = gmysql('db.sqlite3')
        sql = r"delete from contract_list where id=" + ids
        try:
            myd.put_data(sql)
            ret = utils.okmsg('成功删除')
        except Exception as e:
            ret = utils.failmsg('删除出错 ：' + str(e))
        return jsonify(ret)
    elif wdo == 'openmod_e':  # 修改或增加记录
        if ids == '':  # 打开增加记录窗口
            act = '/get_all_contract/?do=new'
            dat = {'id': ''}  # ,'name':d[1],'date':d[2],'manager':d[3],'buy':d[4]}
        else:  # 打开修改记录窗口
            myd = gmysql('db.sqlite3')
            sql = r"select * from contract_list where id=" + ids
            d = myd.get_data(sql)  # 读取要修改的记录
            act = '/get_all_contract/?do=update'
            dat = {'id': d[0], 'contract_name': d[1], 'file_path': d[2], 'type': d[3]}
        return render_template("mod_download.html", act=act, dat=dat)  # 显示修改页面，同时加载json数据
    elif wdo == 'new':  # 插入记录
        print("new")
        contract_name = utils.input(request, 'contract_name', '')
        type = utils.input(request, 'type', '')
        sql = f"insert into contract_list(contract_name,type) values('{contract_name}','{type}')"
        myd = gmysql('db.sqlite3')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    elif wdo == 'update':  # 修改记录
        contract_name = utils.input(request, 'contract_name', '')
        type = utils.input(request, 'type', '')
        sql = f"update  contract_list set contract_name='{contract_name}',type='{type}' where id={ids}"
        print(f'update_sql:{sql}')
        myd = gmysql('db.sqlite3')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    else:
        act = '/get_all_contract/'  # 定义 act 变量，确保在所有使用场景下都已定义
        return render_template("list.html", act=act)

# 合同下载
@app.route('/download_file/', methods=["GET", "POST"])
def download_file():
    filename = utils.input(request, 'filename', '')
    try:
        resp = {
            "file_path": f"/static/uploads/{filename}"
        }
        print(resp)
        # return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
        return jsonify(resp)
    except FileNotFoundError:
        print("没有该名称的模板")
        abort(404)


# 工作事件crud
@app.route('/get_eventlist/', methods=["GET", "POST"])  # 路由－－对应执行的函数
def get_eventlist():
    wdo = utils.input(request, 'do', '')
    ids = utils.input(request, 'id', '')
    page = utils.input(request, 'page', '')
    limit = utils.input(request, 'limit', '')
    if wdo == '':  # 什么子操作都没有 则加载list.html显示表格
        act = '/get_eventlist/'
        return render_template("get_eventlist.html", act=act)
    elif wdo == 'getdata':  # 前端HTML页面通过JS，向后台申请数据
        nms = utils.input(request, 'name', '')  # 取前端回传的 name 参数
        page = int(page) if page.isdigit() else 1
        limit = int(limit) if limit.isdigit() else 10
        offset = (page - 1) * limit  # 计算偏移量
        myd = gmysql('db.sqlite3')  # 打开数据库
        sql = r"select id,name,start,end_time,progress,step,note from process"  # SQL命令
        count_sql = "SELECT COUNT(*) FROM process"  # 用于计算总数的SQL
        if nms:  # 如果查询 name字段
            sql += f" WHERE name LIKE '%%{nms}%%'"  # 增加查询SQL内容
            count_sql += f" WHERE name LIKE '%%{nms}%%'"  # 同步修改计数SQL
        print(f"nms:{nms}")
        sql += f" LIMIT {limit} OFFSET {offset}"  # 添加LIMIT和OFFSET用于分页

        data = myd.get_data(sql, 1)  # 取数据
        total_count = myd.get_data(count_sql, 0)  # 获取总记录数，返回形式如 (5,)
        if total_count is not None:
            total_count = total_count[0]  # 提取总记录数
        else:
            total_count = 0  # 如果无法获取，设为0
        dat = []
        for d in data:  # 将数据行变成JSON列表。
            # sql = r"select id,name,start,end_time,progress,step,note from process"  # SQL命令
            t = {'id': d[0], 'name': d[1], 'start': d[2], 'end_time': d[3], 'progress': d[4], 'step': d[5], 'note': d[6]}
            dat.append(t)
        resp_data = {
            'code': 0,
            'msg': "success",
            'count': total_count,  # 返回总记录数
            'data': dat
        }
        return jsonify(resp_data)  # 发回前端显示
    elif wdo == 'delrow':  # 删除记录
        print("删除")
        myd = gmysql('db.sqlite3')
        sql = r"delete from process where id=" + ids
        try:
            myd.put_data(sql)
            ret = utils.okmsg('成功删除')
        except Exception as e:
            ret = utils.failmsg('删除出错 ：' + str(e))
        return jsonify(ret)
    elif wdo == 'openmod_e':  # 修改或增加记录
        if ids == '':  # 打开增加记录窗口
            act = '/get_eventlist/?do=new'
            dat = {'id': ''}  # ,'name':d[1],'date':d[2],'manager':d[3],'buy':d[4]}
        else:  # 打开修改记录窗口
            myd = gmysql('db.sqlite3')
            sql = r"select * from process where id=" + ids
            d = myd.get_data(sql)  # 读取要修改的记录
            act = '/get_eventlist/?do=update'
            dat = {'id': d[0], 'name': d[1], 'start': d[2], 'end_time': d[3], 'progress': d[4], 'step': d[5],
                   'note': d[6]}
        return render_template("mod_work.html", act=act, dat=dat)  # 显示修改页面，同时加载json数据
    elif wdo == 'new':  # 插入记录
        print("new")
        name = utils.input(request, 'name', '')
        start = utils.input(request, 'start', '')
        end_time = utils.input(request, 'end_time', '')
        progress = utils.input(request, 'progress', '')
        step = utils.input(request, 'step', '')
        note = utils.input(request, 'note', '')
        sql = f"insert into process(name,start,end_time,progress,step,note) values('{name}','{start}','{end_time}','{progress}','{step}','{note}')"
        myd = gmysql('db.sqlite3')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    elif wdo == 'update':  # 修改记录
        name = utils.input(request, 'name', '')
        start = utils.input(request, 'start', '')
        end_time = utils.input(request, 'end_time', '')
        progress = utils.input(request, 'progress', '')
        step = utils.input(request, 'step', '')
        note = utils.input(request, 'note', '')
        sql = f"update  process set name='{name}',start='{start}',end_time='{end_time}',progress='{progress}',step='{step}',note='{note}' where id={ids}"
        print(f'update_sql:{sql}')
        myd = gmysql('db.sqlite3')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    else:
        act = '/get_eventlist/'  # 定义 act 变量，确保在所有使用场景下都已定义
        return render_template("list.html", act=act)


@app.route("/index", methods=["GET", "POST"])  # 路由－－对应执行的函数
# @app.route('/', methods=["GET", "POST"])  # url='/'和'/index'时，跳到主页显示
def home():
    myd = gmysql('db.sqlite3')  # 使用初始化后的gmysql对象
    sql = "SELECT id, title, content, notice_url, create_time FROM news"
    data = myd.get_data(sql, 1)  # 获取全部数据
    dat = []
    if data:
        for d in data:  # 将数据行变成JSON列表
            t = {'id': d[0], 'title': d[1], 'content': d[2], 'notice_url': d[3], 'create_time': d[4]}
            dat.append(t)

    # 计算数据总数
    count_data = myd.get_data("SELECT COUNT(*) FROM data", 0)
    count_process = myd.get_data("SELECT COUNT(*) FROM process", 0)
    count_contract_list = myd.get_data("SELECT COUNT(*) FROM contract_list", 0)

    # 检查数据总数查询结果并处理可能的 None 值
    count_data = count_data[0] if count_data else 0
    count_process = count_process[0] if count_process else 0
    count_contract_list = count_contract_list[0] if count_contract_list else 0

    # 渲染模板并返回页面
    return render_template('index.html', dat=dat, count_data=count_data,count_process=count_process, count_contract_list=count_contract_list,web_path='index')


@app.route('/8ad9min0124', methods=["GET", "POST"])  # 管理登录
def adm_auth():
    if request.method == "GET":  # 不是post则显示登录页面
        return render_template('/admin/admlog.html')
    else:  # post说明是提交登录
        return auth_adm(request)  # 跳去认证登录


@app.route("/admindex/", methods=["GET", "POST"])
def admhome():
    return list(request)  # 所有的admin请求都由list函数处理


# 告警信息汇总模块
@app.route("/admin_warning/", methods=["GET", "POST"])
def admin_warning():
    wdo = utils.input(request, 'do', '')
    ids = utils.input(request, 'id', '')
    page = utils.input(request, 'page', '')
    limit = utils.input(request, 'limit', '')
    if wdo == '':  # 什么子操作都没有 则加载list.html显示表格
        act = '/admin_warning/'
        return render_template("admin/admin_warning.html", act=act,web_path='admin_warning')
    elif wdo == 'getdata':  # 前端HTML页面通过JS，向后台申请数据
        url = utils.input(request, 'url', '')  # 接收前端参数 url
        page = int(page) if page.isdigit() else 1
        limit = int(limit) if limit.isdigit() else 10
        offset = (page - 1) * limit  # 计算偏移量
        myd = gmysql('adm.db')
        sql = r"SELECT id, put_time, type, ip, url, info FROM log ORDER BY put_time DESC"  # SQL命令，增加了ORDER BY子句
        count_sql = "SELECT COUNT(*) FROM log"  # 用于计算总数的SQL
        if url:  # 如果查询 url
            sql += f" WHERE url LIKE '%%{url}%%'"  # 增加查询SQL内容
            count_sql += f" WHERE url LIKE '%%{url}%%'"  # 同步修改计数SQL
        print(f"url: {url}")
        sql += f" LIMIT {limit} OFFSET {offset}"  # 添加LIMIT和OFFSET用于分页
        data = myd.get_data(sql, 1)  # 取数据
        total_count = myd.get_data(count_sql, 0)  # 获取总记录数，返回形式如 (5,)
        if total_count is not None:
            total_count = total_count[0]  # 提取总记录数
        else:
            total_count = 0  # 如果无法获取，设为0
        dat = []
        for d in data:  # 将数据行变成JSON列表
            # 使用unquote函数解码
            decoded_str = unquote(d[5])

            t = {'id': d[0], 'put_time': d[1], 'type': d[2], 'ip': d[3], 'url': d[4], 'info': decoded_str}
            dat.append(t)
        resp_data = {
            'code': 0,
            'msg': "success",
            'count': total_count,  # 返回总记录数
            'data': dat
        }
        print(resp_data)
        return jsonify(resp_data)  # 发回前端显示
    elif wdo == 'delrow':  # 删除记录
        print("删除")
        myd = gmysql('adm.db')
        sql = r"delete from log where id=" + ids
        try:
            myd.put_data(sql)
            ret = utils.okmsg('成功删除')
        except Exception as e:
            ret = utils.failmsg('删除出错 ：' + str(e))
        return jsonify(ret)
    elif wdo == 'openmod_e':  # 修改或增加记录
        if ids == '':  # 打开增加记录窗口
            act = '/admin_warning/?do=new'
            dat = {'id': ''}  # ,'name':d[1],'date':d[2],'manager':d[3],'buy':d[4]}
        else:  # 打开修改记录窗口
            myd = gmysql('adm.db')
            sql = r"select * from log where id=" + ids
            d = myd.get_data(sql)  # 读取要修改的记录
            act = '/admin_warning/?do=update'
            dat = {'id': d[0], 'put_time': d[1], 'type': d[2], 'ip': d[3], 'url': d[4], 'info': d[5]}
        return render_template("mod_warning.html", act=act, dat=dat)  # 显示修改页面，同时加载json数据
    elif wdo == 'new':  # 插入记录
        print("new")
        put_time = utils.input(request, 'put_time', '')
        type = utils.input(request, 'type', '')
        ip = utils.input(request, 'ip', '')
        url = utils.input(request, 'url', '')
        info = utils.input(request, 'info', '')
        sql = f"insert into log(put_time,type,ip,url,step,info) values('{put_time}','{type}','{ip}','{url}','{info}')"
        myd = gmysql('adm.db')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    elif wdo == 'update':  # 修改记录
        put_time = utils.input(request, 'put_time', '')
        type = utils.input(request, 'type', '')
        ip = utils.input(request, 'ip', '')
        url = utils.input(request, 'url', '')
        info = utils.input(request, 'info', '')
        sql = f"update  log set put_time='{put_time}',type='{type}',ip='{ip}',url='{url}',info='{info}' where id={ids}"
        print(f'update_sql:{sql}')
        myd = gmysql('adm.db')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    else:
        act = '/admin_warning/'  # 定义 act 变量，确保在所有使用场景下都已定义
        return render_template("list.html", act=act)


# sql注入攻击模块
@app.route("/admin_sql/", methods=["GET", "POST"])
def admin_sql():
    wdo = utils.input(request, 'do', '')
    ids = utils.input(request, 'id', '')
    page = utils.input(request, 'page', '')
    limit = utils.input(request, 'limit', '')
    if wdo == '':  # 什么子操作都没有 则加载list.html显示表格
        act = '/admin_sql/'
        return render_template("admin/admin_sql.html", act=act, web_path='admin_sql')
    elif wdo == 'getdata':  # 前端HTML页面通过JS，向后台申请数据
        url = utils.input(request, 'url', '')
        page = int(page) if page.isdigit() else 1
        limit = int(limit) if limit.isdigit() else 10
        offset = (page - 1) * limit
        myd = gmysql('adm.db')
        base_sql = "SELECT id, put_time, type, ip, url, info FROM log WHERE type='SQL' ORDER BY put_time DESC"  # 在基础SQL中添加ORDER BY
        count_sql = "SELECT COUNT(*) FROM log WHERE type='SQL'"
        if url:
            base_sql += f" AND url LIKE '%%{url}%%'"  # 添加URL过滤条件
            count_sql += f" AND url LIKE '%%{url}%%'"

        sql = f"{base_sql} LIMIT {limit} OFFSET {offset}"  # 分页查询
        print(f"url: {url}")

        data = myd.get_data(sql, 1)
        total_count = myd.get_data(count_sql, 0)
        total_count = total_count[0] if total_count else 0

        dat = [{'id': d[0], 'put_time': d[1], 'type': d[2], 'ip': d[3], 'url': d[4], 'info': unquote(d[5])} for d in
               data]

        resp_data = {
            'code': 0,
            'msg': "success",
            'count': total_count,
            'data': dat
        }
        return jsonify(resp_data)
    elif wdo == 'delrow':  # 删除记录
        print("删除")
        myd = gmysql('adm.db')
        sql = r"delete from log where id=" + ids
        try:
            myd.put_data(sql)
            ret = utils.okmsg('成功删除')
        except Exception as e:
            ret = utils.failmsg('删除出错 ：' + str(e))
        return jsonify(ret)
    elif wdo == 'openmod_e':  # 修改或增加记录
        if ids == '':  # 打开增加记录窗口
            act = '/admin_sql/?do=new'
            dat = {'id': ''}  # ,'name':d[1],'date':d[2],'manager':d[3],'buy':d[4]}
        else:  # 打开修改记录窗口
            myd = gmysql('adm.db')
            sql = r"select * from log where id=" + ids
            d = myd.get_data(sql)  # 读取要修改的记录
            act = '/admin_sql/?do=update'
            dat = {'id': d[0], 'put_time': d[1], 'type': d[2], 'ip': d[3], 'url': d[4], 'info': d[5]}
        return render_template("admin/admin_sql.html", act=act, dat=dat, web_path='admin_sql')  # 显示修改页面，同时加载json数据
    elif wdo == 'new':  # 插入记录
        print("new")
        put_time = utils.input(request, 'put_time', '')
        type = utils.input(request, 'type', '')
        ip = utils.input(request, 'ip', '')
        url = utils.input(request, 'url', '')
        info = utils.input(request, 'info', '')
        sql = f"insert into log(put_time,type,ip,url,step,info) values('{put_time}','{type}','{ip}','{url}','{info}')"
        myd = gmysql('adm.db')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    elif wdo == 'update':  # 修改记录
        put_time = utils.input(request, 'put_time', '')
        type = utils.input(request, 'type', '')
        ip = utils.input(request, 'ip', '')
        url = utils.input(request, 'url', '')
        info = utils.input(request, 'info', '')
        sql = f"update  log set put_time='{put_time}',type='{type}',ip='{ip}',url='{url}',info='{info}' where id={ids}"
        print(f'update_sql:{sql}')
        myd = gmysql('adm.db')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    else:
        act = '/admin_sql/'  # 定义 act 变量，确保在所有使用场景下都已定义
        return render_template("list.html", act=act)


# 暴力破解尝试
@app.route("/admin_violence/", methods=["GET", "POST"])
def admin_violence():
    wdo = utils.input(request, 'do', '')
    ids = utils.input(request, 'id', '')
    page = utils.input(request, 'page', '')
    limit = utils.input(request, 'limit', '')
    if wdo == '':  # 什么子操作都没有 则加载list.html显示表格
        act = '/admin_violence/'
        return render_template("admin/admin_violence.html", act=act, web_path='admin_violence')
    elif wdo == 'getdata':  # 前端HTML页面通过JS，向后台申请数据
        url = utils.input(request, 'url', '')
        page = int(page) if page.isdigit() else 1
        limit = int(limit) if limit.isdigit() else 10
        offset = (page - 1) * limit
        myd = gmysql('adm.db')
        base_sql = "SELECT id, put_time, type, ip, url, info FROM log WHERE type='HPT' ORDER BY put_time DESC"  # 在基础SQL中添加ORDER BY
        count_sql = "SELECT COUNT(*) FROM log WHERE type='HPT'"
        if url:
            base_sql += f" AND url LIKE '%%{url}%%'"  # 添加URL过滤条件
            count_sql += f" AND url LIKE '%%{url}%%'"

        sql = f"{base_sql} LIMIT {limit} OFFSET {offset}"  # 分页查询
        print(f"url: {url}")

        data = myd.get_data(sql, 1)
        total_count = myd.get_data(count_sql, 0)
        total_count = total_count[0] if total_count else 0

        dat = [{'id': d[0], 'put_time': d[1], 'type': d[2], 'ip': d[3], 'url': d[4], 'info': unquote(d[5])} for d in
               data]

        resp_data = {
            'code': 0,
            'msg': "success",
            'count': total_count,
            'data': dat
        }
        return jsonify(resp_data)
    elif wdo == 'delrow':  # 删除记录
        print("删除")
        myd = gmysql('adm.db')
        sql = r"delete from log where id=" + ids
        try:
            myd.put_data(sql)
            ret = utils.okmsg('成功删除')
        except Exception as e:
            ret = utils.failmsg('删除出错 ：' + str(e))
        return jsonify(ret)
    elif wdo == 'openmod_e':  # 修改或增加记录
        if ids == '':  # 打开增加记录窗口
            act = '/admin_violence/?do=new'
            dat = {'id': ''}  # ,'name':d[1],'date':d[2],'manager':d[3],'buy':d[4]}
        else:  # 打开修改记录窗口
            myd = gmysql('adm.db')
            sql = r"select * from log where id=" + ids
            d = myd.get_data(sql)  # 读取要修改的记录
            act = '/admin_violence/?do=update'
            dat = {'id': d[0], 'put_time': d[1], 'type': d[2], 'ip': d[3], 'url': d[4], 'info': d[5]}
        return render_template("admin/admin_violence.html", act=act, dat=dat)  # 显示修改页面，同时加载json数据
    elif wdo == 'new':  # 插入记录
        print("new")
        put_time = utils.input(request, 'put_time', '')
        type = utils.input(request, 'type', '')
        ip = utils.input(request, 'ip', '')
        url = utils.input(request, 'url', '')
        info = utils.input(request, 'info', '')
        sql = f"insert into log(put_time,type,ip,url,step,info) values('{put_time}','{type}','{ip}','{url}','{info}')"
        myd = gmysql('adm.db')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    elif wdo == 'update':  # 修改记录
        put_time = utils.input(request, 'put_time', '')
        type = utils.input(request, 'type', '')
        ip = utils.input(request, 'ip', '')
        url = utils.input(request, 'url', '')
        info = utils.input(request, 'info', '')
        sql = f"update  log set put_time='{put_time}',type='{type}',ip='{ip}',url='{url}',info='{info}' where id={ids}"
        print(f'update_sql:{sql}')
        myd = gmysql('adm.db')
        ret = myd.put_data(sql)
        if ret == 1:
            ret = utils.failmsg('写入出错')
        else:
            ret = utils.okmsg('成功')
        return jsonify(ret)
    else:
        act = '/admin_violence/'  # 定义 act 变量，确保在所有使用场景下都已定义
        return render_template("list.html", act=act)


# 攻击
@app.route("/admin_attack/", methods=["GET", "POST"])
def admin_attack():
    myd = gmysql('adm.db')
    line_sql = 'select count(*) as number,type from log group by type'
    linebar_data = myd.get_data(line_sql, 1)  # 取得数据，加载pei.html页面，把数据传入dat, 供页面的js代码读取显示
    bar_sql = 'select count(*) as number,ip from log group by ip'
    bar_data = myd.get_data(bar_sql, 1)  # 取得数据，加载pei.html页面，把数据传入dat, 供页面的js代码读取显示
    # print(f"柱状图数据返回:{linebar_data}")
    # print(f"饼状图数据返回:{bar_data}")


    bar_data = [{'value': item[0], 'name': item[1]} for item in bar_data]
    print(bar_data)
    return render_template("admin/admin_attack.html", linebar_data=linebar_data, bar_data=bar_data,web_path='admin_attack')


def query_database():
    # 连接数据库
    with sqlite3.connect('adm.db') as conn:
        cursor = conn.cursor()
        # 如果没有提供时间参数，查询所有数据
        cursor.execute("""
                SELECT type, put_time, COUNT(*) as count
                FROM log
                GROUP BY type, put_time
                ORDER BY put_time
            """)
    data = cursor.fetchall()
    return data


@app.route("/admin_honey/", methods=["GET", "POST"])
def admin_honey():
    from collections import defaultdict
    from datetime import datetime
    data = query_database()
    # 准备一个按小时聚合的数据结构
    aggregated_data = defaultdict(lambda: defaultdict(int))

    # 数据聚合
    for attack_type, timestamp, count in data:
        # 将时间戳字符串转换为 datetime 对象
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        # 以日期和小时为键聚合计数
        hour_key = dt.strftime('%Y-%m-%d %H')
        aggregated_data[attack_type][hour_key] += count

    # 准备传递给 ECharts 的数据格式
    echarts_data = [{
        'SQL': sorted((k, v) for k, v in aggregated_data['SQL'].items()),
        'HPT': sorted((k, v) for k, v in aggregated_data['HPT'].items())
    }]

    print(echarts_data)
    return render_template("admin/admin_honey.html", resp=echarts_data,web_path='admin_honey')


@app.route('/logout/')  # 要登出时
def logout():
    session.pop("user_id")  # 删除session
    return redirect("/login")  # 跳到登录页面

@app.route('/logout_admin/')  # 要登出时
def logout_admin():
    session.pop("user_id")  # 删除session
    return redirect("/8ad9min0124")  # 跳到登录页面

@app.route('/login', methods=["GET", "POST"])  # url==/login时
def login_process():
    if request.method == "GET":  # 不是post则显示登录页面
        # return render_template("login.html")
        return render_template("login_new.html")
    else:  # post说明是提交登录
        username = request.form['username']
        password = request.form['password']
        myd = gmysql('db.sqlite3')
        sql = r"select id,username from auth_user where username='%s' and password='%s'" % (username, password)
        print(sql)
        try:
            dat = myd.get_data(sql, 0)
            if dat:
                # 登录成功，将用户信息存储到会话中
                session['user_id'] = dat[0]  # 设置一个用户 ID 作为示例
                session['username'] = dat[1]
                # 重定向到主页
                return redirect('/index')
            else:
                # 登录失败，返回错误信息
                return 'SQLite系统提示：用户名或密码错误'
                # return render_template("login.html",msg="用户名或者密码错误")
        except Exception as e:
            errmsg = str(e)
            print(errmsg)
            return ' SQLite系统提示 <br>' + errmsg + '<br>用户名或密码错误'


@app.route('/front_index', methods=["GET", "POST"])  # url='/'和'/index'时，跳到主页显示
@app.route('/', methods=["GET", "POST"])  # url='/'和'/index'时，跳到主页显示
def front_index():
    return render_template('front_index.html')


def web_server():  # 启动WEB服务，使用8020端口
    app.run(port=8020, host="0.0.0.0", debug=True)


def eval_server():  # 启动蜜罐服务，使用8308端口
    honeypot.run(8308)


if __name__ == "__main__":
    pool = Pool(2)  # 进程池内设置2个进程
    pool.apply_async(eval_server, args=())  # 1个进程启动蜜罐服务
    pool.apply_async(web_server, args=())  # 1个进程启动WEB服务
    # 此代码目的是并行运行两个单独的服务器进程
    pool.close()
    pool.join()
    # user' or 1 and 1 --
