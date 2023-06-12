# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WebscrapyItem(scrapy.Item):
    name = scrapy.Field()
    rating = scrapy.Field()
    info = scrapy.Field()
    length = scrapy.Field()
    abstract = scrapy.Field()
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
