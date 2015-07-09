# -*- coding: utf-8 -*-
import scrapy
from scrapy import Spider,  Request

import bs4

from scrapyscrappers.items import ScrapyscrappersItem
from scrapyscrappers.util import obtain_keywords,  obtain_locations,  current_datetime,  \
    datetimestr2datetime,  datetime2datetimestr, timeago2datetimestr

class SimplyhiredSpider(Spider):
    name = "simplyhiredspider"
    allowed_domains = ["www.simplyhired.com"]
    base_url = 'www.simplyhired.com'
    query_url = 'https://www.simplyhired.com/search?q=%(keyword)s'

    def __init__(self, keywords="", locations="",  *args, **kwargs):
        self.logger.debug('in init')
        # to call the spider with keywords and locations arguments
        super(SimplyhiredSpider, self).__init__(*args, **kwargs)
        self.keywords = keywords or obtain_keywords()
        self.locations = locations or obtain_locations()

    def start_requests(self):
        self.logger.debug('in start requests')
        for location in self.locations:
            for keyword in self.keywords:
                url_params = {'keyword': keyword,  'location': location}
                url = self.query_url % url_params
                self.logger.debug('request url %s' % url)
                yield Request(url, meta={'keyword': keyword})

    def parse_item(self,  response):
        self.logger.debug('parse_item %s' % response.url)
        item = response.meta['item']
        try:
            item['description'] = response.css('div.detail')[0].extract()
            #item['description'] = response.css('div.description-full::text')[0].extract()
        except IndexError:
            self.logger.debug('error parsing description')
        yield item

    def parse(self, response):
        self.logger.debug('in parse')
#        # with scrapy selector
#        # for sel in response.xpath('//div[@class="job"]'):
#        for sel in response.css('div.job'):
#            item = ScrapyscrappersItem()
#            item['keyword'] = response.meta['keyword']
#            item['date_search'] = current_datetime()
#            #this works, but return different url
#            #item['item_url'] = sel.css('a.title::attr(href)').extract()[0]
#            item['item_url'] =[tool.css('a::attr(href)')[0].extract() for tool in sel.css('div.tools')][0]
#            item['title'] = sel.css('a.title::text').extract()[0].strip()

        # with bs4
        soup = bs4.BeautifulSoup(response.body)
        soupitems = soup.select('div.job')     
        for soupitem in soupitems:
            self.logger.debug('parsing')
            item = ScrapyscrappersItem()
            item['keyword'] = response.meta['keyword']
            item['date_search'] = current_datetime()
            item['item_url'] = [a.attrs.get('href') for a in soupitem.select('div.tools > a') if a.attrs.get('href')][0]
            item['title'] = soupitem.select('h2')[0].text.strip()
            try:
                item['company'] = soupitem.h4.text
            except AttributeError:
                pass
            #      logger.debug('item: %s has no h4 tag' % i)
            if soupitem.find('span', itemprop="addressLocality"):
                item['locality'] = soupitem.find('span', itemprop="addressLocality").text
            if soupitem.find('span', itemprop="addressRegion"):
                item['region'] = soupitem.find('span', itemprop="addressRegion").text
            item['short_description'] = soupitem.find('p', itemprop="description").text
            item['published'] = timeago2datetimestr(item['date_search'],  soupitem.select('span.ago')[0].text)
            #salary
            #clearance
            #department
            #description

            self.logger.debug('title %s' % item['title'])
            yield Request(item['item_url'],  callback=self.parse_item, meta={'item': item} )

        #for url in response.xpath('//link[@rel="next"]/@href').extract()[0]:
        next = response.css('a.next::attr(href)').extract()
        if next:
            self.logger.debug('next url: %s' % next[0] )
            yield Request(next[0], callback=self.parse, meta={'keyword': response.meta['keyword']})