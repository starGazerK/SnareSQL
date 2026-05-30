import sqlite3


class gmysql:
    def __init__(self, dbname):
        self.dbname = dbname

    def get_data(self, sql, mode=0):  # mode=0表示只取一条数据# get_data: 执行SQL查询，并返回结果集。
        con = sqlite3.connect(self.dbname)
        cursorObj = con.cursor()
        cursorObj.execute(sql)
        con.commit()
        if mode != 0:
            rrs = cursorObj.fetchall()
        else:
            rrs = cursorObj.fetchone()
        cursorObj.close()
        con.close()
        return rrs

    def put_data(self, sql):  # put_data: 执行SQL插入、更新、删除等操作，并返回执行结果。
        try:

            con = sqlite3.connect(self.dbname)
            cursorObj = con.cursor()
            cursorObj.execute(sql)
            con.commit()
            con.close()
            res = 0
        except Exception as e:
            print("put_data 出错：%s" % str(e))
            res = 1
        return res

# 这段代码是一个Python类，名为gmysql，用于连接和操作SQLite数据库。在类中定义了一些方法，包括：
#
# conn: 连接到SQLite数据库。
# get_data: 执行SQL查询，并返回结果集。
# put_data: 执行SQL插入、更新、删除等操作，并返回执行结果。
# get_ns: 从列表中找到指定元素，并返回其特定位置的值。
# get_user_data: 查询并返回user表中的数据。
# create_tables: 创建数据库表，并插入一些示例数据。
# 类的实例被创建并存储在变量myd中，而变量log_info则没有被赋值。这段代码执行后，会连接到SQLite数据库，并创建名为user和img的两个表。在user表中插入了四行数据，而在img表中插入了四行数据。如果这些表已经存在，则不会重新创建它们。
