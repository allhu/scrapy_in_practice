# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class RentItem(scrapy.Item):
    '''
    item类
    '''
    title = scrapy.Field()          # 标题
    rent_desc = scrapy.Field()      # 描述
    url = scrapy.Field()            # 详情的url
    pic_list = scrapy.Field()       # 图片列表

