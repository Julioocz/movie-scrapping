# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MovieScrappingItem(scrapy.Item):
    weekday = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    hours = scrapy.Field()
    popularity = scrapy.Field()
    vote_average = scrapy.Field()
    overview = scrapy.Field()

    


