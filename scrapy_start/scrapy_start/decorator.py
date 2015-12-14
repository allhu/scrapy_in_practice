# -*- coding: utf-8 -*-

import functools
import logging

def check_spider_pipeline(process_item_method):
    """
    该注解用在pipeline上
    :param process_item_method:
    :return:
    """
    @functools.wraps(process_item_method)
    def wrapper(self, item, spider):

        # message template for debugging
        msg = '%%s %s pipeline step' % (self.__class__.__name__,)

        # if class is in the spider's pipeline, then use the
        # process_item method normally.
        if self.__class__ in spider.pipeline:
            logging.info(msg % 'executing')
            return process_item_method(self, item, spider)

        # otherwise, just return the untouched item (skip this step in
        # the pipeline)
        else:
            logging.info(msg % 'skipping')
            return item

    return wrapper