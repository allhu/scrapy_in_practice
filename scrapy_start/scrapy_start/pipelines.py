# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import time
from twisted.enterprise import adbapi
from scrapy_start.decorator import check_spider_pipeline
from scrapy_start.qiniu_cloud import QiniuCloud
from hashlib import md5

class RentMySQLPipeline(object):
    '''
    A pipeline to store the time in a MySQL database.
    This implementation uses Twisted's asynchronous database API.
    将租房的信息保存到mysql中.
    '''

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        '''加载mysql配置'''
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            use_unicode=True
        )

        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
        return cls(dbpool)

    @check_spider_pipeline
    def process_item(self, item, spider):
        '''
        pipeline的回调.
        注解用于pipeline与spider之间的对应，只有spider注册了该pipeline，pipeline才会被执行
        '''

        # run db query in the thread pool，在独立的线程中执行
        deferred = self.dbpool.runInteraction(self._do_upsert, item, spider)
        deferred.addErrback(self._handle_error, item, spider)
        # 当_do_upsert方法执行完毕，执行以下回调
        deferred.addCallback(self._get_id_by_guid)

        # at the end, return the item in case of success or failure
        # deferred.addBoth(lambda _: item)
        # return the deferred instead the item. This makes the engine to
        # process next item (according to CONCURRENT_ITEMS setting) after this
        # operation (deferred) has finished.
        time.sleep(10)
        return deferred

    def _do_upsert(self, conn, item, spider):
        '''
        perform an insert.
        将新的item插入数据库，通过url的md5判重.
        '''

        guid = self._get_guid(item)
        now_utc = int(time.time())
        exist_sql = """SELECT EXISTS(SELECT 1 FROM rent_test WHERE guid = %s);"""
        insert_sql = """INSERT INTO rent_test(title, rent_desc, url, guid)
                        VALUES (%s, %s, %s, %s)
                     """

        # 1. 通过url查询该数据是否存在，不存在则保存
        conn.execute(exist_sql, (guid,))
        ret = conn.fetchone()[0]
        if ret:
            logging.warn('item already exists, guid: {0}, url: {1}'.format(guid, item['url']))
            return None
        else:
            conn.execute(insert_sql, (item['title'], item['rent_desc'], item['url'], guid))
            logging.info("item stored in db, guid: {0}, url: {1}".format(guid, item['url']))
            return item

    def _get_id_by_guid(self, item):
        """
        通过guid查询刚才插入的数据的id
        :param pic_list:
        :param item:
        :param spider:
        :return:
        """
        logging.info('in _get_id_by_guid()......')
        if item is None or item['pic_list'] is None or len(item['pic_list']) == 0:
            logging.warn('item is None, or pic_list is empty')
            return None

        guid = self._get_guid(item)
        get_id_sql = """SELECT id FROM rent_test WHERE guid = '{0}' LIMIT 1;
                     """.format(guid)
        defer = self.dbpool.runQuery(get_id_sql)
        # 增加回调，当查询到id后，将图片列表保存到七牛
        defer.addCallbacks(self._upload_and_save_pic_list, callbackArgs=(item['pic_list'],))
        logging.info('addCallback _upload_pic_list done')
        time.sleep(10)
        return item

    def _upload_and_save_pic_list(self, info_id_list, pic_list):
        """
        将图片列表上传到七牛，然后保存到数据库
        :param info_id_list:
        :param pic_list:
        :return:
        """
        insert_pic_sql = """INSERT INTO rent_pic_test (rent_id, pic_url) VALUES ({0}, '{1}');"""
        info_id = info_id_list[0][0]
        qiniu_cloud = QiniuCloud()
        pic_key_list = qiniu_cloud.upload_pic_list(key_prefix='rent/', info_id=info_id, pic_list=pic_list,
                                                   insert_pic_sql=insert_pic_sql)
        logging.info('pic_key_list: {0}'.format(pic_key_list))
        if pic_key_list is None or len(pic_key_list) == 0:
            logging.error('pic_key_list is empty...')
            return False

        # insert_pic_sql = """INSERT INTO rent_pic (rent_id, pic_url) VALUES ({0}, '{1}');"""
        # for (info_id, pic_key) in pic_key_list:
        #     self.dbpool.runOperation(insert_pic_sql.format(info_id, pic_key))
        #     logging.info('save pic to DB done, pic_key: {0}'.format(pic_key))

        return True

    def _handle_error(self, failure, item, spider):
        """
        Handle occurred on db interaction
        :param failure:
        :param item:
        :param spider:
        :return:
        """
        logging.error(failure)

    def _get_guid(self, item):
        """
        Generate an unique identifier for a give item
        :param item:
        :return:
        """
        return md5(item['url']).hexdigest()
