# -*- coding: utf-8 -*-

__author__ = 'nkcoder'
from scrapy import FormRequest, Request, Spider
import logging

class RentSpider(Spider):
    """
    爬取一个需要登录才能看到页面内容的网站数据，非真实帐号，模拟登录的过程可以参考。
    """
    name = 'fish_saying'
    allowed_domains = ['fishsaying.com']
    login_url = 'http://cp.fishsaying.com/'
    start_urls = [
        'http://cp.fishsaying.com/notifications/index'
        ]
    # 应该交给哪个pipeline去处理
    pipeline = set([

    ])

    # 伪装头部，有些网站是必须的
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate",
        "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "Referer": "http://cp.fishsaying.com"
    }

    # 两种实现方式都可以的，注意：有些情况下（比如本例），headers参数是必不可少的，否则登录成功后，
    # 后续的请求还是会显示未登录！

    # 1. 在start_request中通过FormRequest()
    # def start_requests(self):
    #     logging.info('in start_request...')
    #     form_data = {'username': '123456@qq.com', 'password': '123456', 'remember_me': '1'}
    #
    #     return [FormRequest(self.login_url,
    #                                     headers = self.headers,
    #                                     formdata=form_data,
    #                                     callback=self.after_login,
    #                                     dont_filter=True
    #                                       )]

    # 2. 在默认的回调方法parse()中，通过FormReuqest.from_response()请求(非真实帐号)
    def parse(self, response):
        form_data = {'username': '123456@qq.com', 'password': '123456', 'remember_me': '1'}
        return FormRequest.from_response(response,
                                         headers=self.headers,
                                         formxpath='//form[@class="form-login"]',
                                         formdata=form_data,
                                         callback=self.after_login,
                                         )


    def after_login(self, response):
        """
        登录成功后，爬取需要登录的页面的数据
        :param response:
        :return:
        """
        logging.info('in after_login, response: {0}'.format(response.body))

        for url in self.start_urls:
            yield Request(url=url,
                            callback=self.parse_item,
                            headers=self.headers,
                            dont_filter=True)

    def parse_item(self, response):
        """
        分析并爬取数据
        :param response:
        :return:
        """
        logging.info('in parse_item...')

        feed_list = response.xpath('//div[@class="feed-activity-list"]/div[@class="feed-element"]')
        for feed in feed_list:
            feed_content = feed.xpath('string(.)').extract_first()
            logging.info('feed_content: {}'.format(feed_content.encode('utf-8')))






