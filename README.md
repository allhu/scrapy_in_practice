使用Scrapy框架爬取网页的一些示例，给大家一个参考，也给自己做个备忘。

关于搭建Scrapy爬虫开发环境，请参考文章[搭建Scrapy爬虫的开发环境](http://nkcoder.github.io/2015/11/17/Scrapy-crawl-intro-install-and-config/).

目前仅包含两个爬虫：fish_saying spider和xiaochuncnjp spider。

### fish_saying spider

- 爬取一个需要登录才能看到数据的页面;
- 使用FormRequest和FormRequest.from_response模拟登录过程;
- 使用XPath分析页面结构；

### xiaochuncnjp spider

- 爬取一个论坛，论坛的大图需要登录才能查看图片；
- 使用XPath分析页面结构；
- 使用MySQL存储数据；
- 使用七牛存储图片；

### 运行爬虫

	GuoDaniel:python nkcoder$ cd scrapy_in_practice/
	GuoDaniel:scrapy_in_practice nkcoder$ cd scrapy_start/
	GuoDaniel:scrapy_start nkcoder$ ls
	scrapy.cfg	scrapy_start
	GuoDaniel:scrapy_start nkcoder$ source ../scrapy_env/bin/activate
	(scrapy_env) GuoDaniel:scrapy_start nkcoder$ scrapy list
	fish_saying
	xiaochuncnjp
	(scrapy_env) GuoDaniel:scrapy_start nkcoder$ scrapy crawl fish_saying
