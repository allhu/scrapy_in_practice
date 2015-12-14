# -*- coding: utf-8 -*-

import logging
import re

from scrapy import Spider, FormRequest, Request
from scrapy_start import pipelines
from scrapy_start.items import RentItem

class RentSpider(Spider):
    """
    爬取论坛数据示例：要爬取的页面需要登录才能查看大图
    """
    name = 'xiaochuncnjp'
    allowed_domains = ['xiaochuncnjp.com']
    # 要爬取的url
    start_urls = [
        'http://www.xiaochuncnjp.com/forum.php?mod=forumdisplay&fid=69&filter=typeid&typeid=62'
        ]

    # 应该交给哪个pipeline去处理
    pipeline = set([
        pipelines.RentMySQLPipeline,
    ])

    # 伪装头部
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate",
        "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "Referer": "http://www.xiaochuncnjp.com"
    }

    def parse(self, response):
        """
        这是默认的回调方法，得到response后：
        1. 如果需要登录，则先通过FormRequest登录论坛；
        2. 如果不需要登录，通过Request继续请求；
        :param response:
        :return:
        """
        # 需要登录，使用FormRequest.from_response模拟登录
        if 'id="lsform"' in response.body:
            logging.info('in parse, need to login, url: {0}'.format(response.url))
            form_data = {'handlekey': 'ls', 'quickforward': 'yes', 'username': 'daniell123', 'password': 'admin123'}
            request = FormRequest.from_response(response=response,
                                                headers=self.headers,
                                                formxpath='//form[contains(@id, "lsform")]',
                                                formdata=form_data,
                                                callback=self.parse_list
                                                )
        else:
            logging.info('in parse, NOT need to login, url: {0}'.format(response.url))
            request = Request(url=response.url,
                              headers=self.headers,
                              callback=self.parse_list,
                              )

        yield request

    def parse_list(self, response):
        """
        要爬取的租房信息可以分解成一个列表，遍历列表，逐一请求处理
        :param response:
        :return:
        """
        logging.info('in parse_list, response: {0}'.format(response.body))
        if u'登录失败'.encode('utf-8') in response.body:
            logging.error('login failed.')
            return

        # 解析出租房列表，然后遍历
        base_url = 'http://www.xiaochuncnjp.com/'
        tbody_list = response.xpath('//div/div/form/table/tbody[contains(@id, "normalthread")]')
        for index, tbody in enumerate(tbody_list):
            # todo: for test
            if index >= 10:
                logging.info('index = {0}, breaking...'.format(index))
                break
            rent_item = RentItem()

            # 解析标题和详情页面的url
            title_a = tbody.xpath('tr/th/a[contains(@class, "s xst")]')
            rent_item['title'] = title_a.xpath('string(.)').extract_first()
            rent_item['url'] = base_url + title_a.xpath('./@href').extract_first()

            logging.info('title: {0}, url: {1}'.format(rent_item['title'].encode('utf-8'), rent_item['url']))

            # 解析详情页的租房描述和图片列表
            request = Request(url=rent_item['url'],
                              headers=self.headers,
                              callback=self.parse_item,
                              meta={'rent_item': rent_item}
                              )
            yield request

    def parse_item(self, response):
        """
        解析每一条租房信息的描述和图片列表
        :param response:
        :return:
        """
        rent_item = response.meta['rent_item']

        # 解析描述
        td = response.xpath('//div[@class = "pcb"]')[0].xpath('div[contains(@class, "t_fsz")]/table/tr/td[1]')
        # 这里的content包含了图片的相关说明文字，因此需要从中排除
        content = td.xpath('string(.)').extract_first()

        # 1. 先从中文里取图片，即td下找图片列表
        pic_list = []
        image_list = td.xpath('.//ignore_js_op')
        if image_list:
            for index, image in enumerate(image_list):
                if index > 12:
                    logging.warn("too many images, only keep 12.")
                    break
                pic_url = image.xpath('.//img/@file').extract_first()
                if not pic_url:
                    pic_url = image.xpath('.//img/@src').extract_first()
                if pic_url:
                    pic_list.append(pic_url)
                pic_text = image.xpath('string(.)').extract_first()
                if pic_text in content:
                    logging.info('replace pic_text in content, pic_text: {0}'.format(pic_text.encode('utf-8')))
                    # 将图片中的问题从content中去除
                    content = content.replace(pic_text, '')

        # 2. 如果没找到，则从‘更多图片’的地方找，即imagelist_，注意取大图
        if not pic_list:
            logging.info('no images found in content, try in extra info.')
            div_list = response.xpath('//div[@class = "pcb"]')[0].xpath('div[contains(@class, "t_fsz")]/div/div[contains(@id, "imagelist_")]/ignore_js_op')
            if div_list:
                for div in div_list:
                    img_url = div.xpath('.//img/@file').extract_first()
                    if img_url:
                        pic_list.append(img_url)

        rent_item['pic_list'] = pic_list

        # 对描述做进一步处理，比如去掉多于的换行和空格等
        content = re.sub(u'本帖最后由.*编辑', '', content)
        content = content.replace(u'\xa0', u'\n')
        content = re.sub(' +\n\n +', '\n', content)
        content = re.sub('(\r\n)+', '\n', content)
        content = re.sub('\n{3,}', '\n\n', content)
        rent_item['rent_desc'] = content

        logging.info('rent_item: {0}'.format(rent_item))
        return rent_item