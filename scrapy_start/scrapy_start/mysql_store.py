# -*- coding: utf-8 -*-

import logging
import MySQLdb as mdb
import settings


class MySQLStore(object):
    """
    操作数据库，通过adbapi实现时
    """

    def __init__(self):
        self.connect = mdb.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER,
                       passwd=settings.MYSQL_PASSWD, db=settings.MYSQL_DBNAME)

    def select_one_data(self, query_sql):
        """
        查询数据
        :param query_sql:   查询的sql
        :return:            返回一个tuple，如(36, )，通过result[0]取值
        """
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(query_sql)
            result = cursor.fetchone()
            logging.info('select data done, query_sql: {0}'.format(query_sql))
            return result

    def insert_data(self, insert_sql):
        """
        插入数据
        :param insert_sql:  插入的sql
        :return:
        """
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(insert_sql)
            logging.info('insert data done, insert_sql: {0}'.format(insert_sql))




