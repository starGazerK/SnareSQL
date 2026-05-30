from flask import *
from common import utils
from common.mysqllib import gmysql
from os import urandom
import urllib
def auth_adm(request):  # post提交登录admin
    username = request.form['username']
    password = request.form['password']        
    try:
        with open('admin.txt','r') as f:
            ss=f.read().strip()
        rr=ss.split('@')
    except:
        rr=['admin','admin111']      # 如果没有admin.txt写明管理员帐号密码，则密码和用户名用admin@admin登录
    if username==rr[0] and password==rr[1]:
        session['user_id'] = 99999
        session['username'] = rr[0]
        print('yes admin login ok')
        #return redirect('/admindex/')   # 跳到管理员页面
        return render_template('admindex.html',web_path="8ad9min0124")
    else:
        return redirect("/8ad9min0124") # 跳到用户登录页面

def list(request):
    wdo = request.args.get('do')
    ret={}
    if  wdo is None or wdo== 'list':        # 显示日志表格页面
        act="/admindex/"
        return render_template('/admindex.html',dat=ret,act=act,web_path='admindex')  # 跳到管理员页面
    elif wdo=='getdata':   # 加载数据
        myd=gmysql('adm.db')
        sql='select * from log order by put_time desc';
        data=myd.get_data(sql,1)  
        dat=[]
        for d in data:
            nr=urllib.parse.unquote(d[5])
            t={'id':d[0],'time':d[1],'type':d[2],'ip':d[3],'url':d[4],'info':nr}
            dat.append(t)
        return jsonify(dat)
    elif wdo=='download':        # 下载日志
        file_path = 'run.log'  
        return send_file(file_path, as_attachment=True)
    elif wdo=='line1':            # 显示结构图1
        myd=gmysql('adm.db')
        sql='select count(*) as number,type from log group by type';        
        data=myd.get_data(sql,1)    # 取得数据，加载pei.html页面，把数据传入dat, 供页面的js代码读取显示
        print(data)
        return render_template('/admin/pei.html',dat=data)  #
    elif wdo=='line2':           # 显示结构图2
        myd=gmysql('adm.db')
        sql='select count(*) as number,ip from log group by ip';        
        data=myd.get_data(sql,1)   # 取得数据，加载pei.html页面，把数据传入dat, 供页面的js代码读取显示
        return render_template('/admin/pei.html',dat=data)  #
    elif wdo=='delrow':          # 删除
        ids = request.args.get('id','')
        if ids=='':
            ret=utils.failmsg('error')
        else:
            myd=gmysql('adm.db')
            sql='delete from log where id='+ids;        
            ret=myd.put_data(sql)  
            if ret==1:
                ret=utils.failmsg('error')
            else:
                ret=utils.okmsg('删除成功')
        return jsonify(ret)