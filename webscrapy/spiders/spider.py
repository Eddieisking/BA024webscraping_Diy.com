"""
Project: Web scraping for customer reviews
Author: Hào Cui
Date: 07/04/2023
"""
import json
import re

import scrapy
from scrapy import Request

from webscrapy.items import WebscrapyItem


class SpiderSpider(scrapy.Spider):
    name = "spider"
    allowed_domains = ["www.diy.com", "api.bazaarvoice.com"]
    headers = {}  #

    def start_requests(self):
        # keywords = ['dewalt', 'Stanley', 'Black+Decker', 'Craftsman', 'Porter-Cable', 'Bostitch', 'Facom', 'MAC Tools', 'Vidmar', 'Lista', 'Irwin Tools', 'Lenox', 'Proto', 'CribMaster', 'Powers Fasteners', 'cub-cadet', 'hustler', 'troy-bilt', 'rover', 'BigDog Mower', 'MTD']
        exist_keywords = ['dewalt', 'stanley tools', 'Black+Decker', 'Craftsman', 'Bostitch', 'Facom', 'Irwin Tools', 'Lenox']
        # company = 'Stanley Black and Decker'

        keywords = ['dewalt']
        # from search words to generate product_urls
        for keyword in keywords:
            push_key = {'keyword': keyword}
            search_url = f'https://www.diy.com/search?term={keyword}'

            yield Request(
                url=search_url,
                callback=self.parse,
                cb_kwargs=push_key,
            )

    def parse(self, response, **kwargs):
        # Extract the pages of product_urls
        page = response.xpath('//*[@id="content"]//main//p[@data-test-id="search-options-total-results"]/text()')[0].extract()

        # Remove any non-digit characters from the string
        number_string = ''.join(filter(str.isdigit, page))

        # Convert the extracted string into an integer
        page_number = int(number_string)

        pages = (page_number // 24) + 1

        # Based on pages to build product_urls
        keyword = kwargs['keyword']
        product_urls = [f'https://www.diy.com/search?page={page}&term={keyword}' for page
                        in range(1, pages)]

        for product_url in product_urls:
            yield Request(url=product_url, callback=self.product_parse)

    def product_parse(self, response: Request, **kwargs):

        product_list = response.xpath('//*[@id="content"]//main//ul/li')

        for product in product_list:
            product_href = product.xpath('.//div[@data-test-id="product-panel"]/a/@href')[0].extract()
            product_detailed_url = f'https://www.diy.com{product_href}'
            yield Request(url=product_detailed_url, callback=self.product_detailed_parse)

    def product_detailed_parse(self, response, **kwargs):

        product_id = response.xpath('.//*[@id="product-details"]//td[@data-test-id="product-ean-spec"]/text()')[
            0].extract()
        product_name = response.xpath('//h1[@id="product-title"]/text()')[0].extract()

        # Product reviews url
        product_detailed_href = f'https://api.bazaarvoice.com/data/reviews.json?resource=reviews&action' \
                                f'=REVIEWS_N_STATS&filter=productid%3Aeq%3A{product_id}&filter=contentlocale%3Aeq%3Aen_FR%2Cfr_FR' \
                                f'%2Cen_US%2Cen_GB%2Cen_GB&filter=isratingsonly%3Aeq%3Afalse&filter_reviews' \
                                f'=contentlocale%3Aeq%3Aen_FR%2Cfr_FR%2Cen_US%2Cen_GB%2Cen_GB&include=authors' \
                                f'%2Cproducts&filteredstats=reviews&Stats=Reviews&limit=8&offset=0&sort' \
                                f'=submissiontime%3Adesc&passkey=7db2nllxwguwj2eu7fxvvgm0t&apiversion=5.5&displaycode' \
                                f'=2191-en_gb '

        if product_detailed_href:
            yield Request(url=product_detailed_href, callback=self.review_parse, meta={'product_name': product_name})

    def review_parse(self, response: Request, **kwargs):
        product_name = response.meta['product_name']
        datas = json.loads(response.body)
        batch_results = datas.get('Results', {})

        offset_number = 0
        limit_number = 0
        total_number = 0

        # if "q1" in batch_results:
        #     result_key = "q1"
        # else:
        #     result_key = "q0"

        offset_number = datas.get('Offset', 0)
        limit_number = datas.get('Limit', 0)
        total_number = datas.get('TotalResults', 0)

        print('offset_number, limit_number, total_number')
        print(offset_number, limit_number, total_number)

        for i in range(limit_number):
            item = WebscrapyItem()
            # results = batch_results.get(result_key, {}).get('Results', [])

            try:
                item['review_id'] = batch_results[i].get('Id', 'N/A')
                item['product_name'] = product_name
                item['customer_name'] = batch_results[i].get('UserNickname', 'Anonymous')
                item['customer_rating'] = batch_results[i].get('Rating', 'N/A')
                item['customer_date'] = batch_results[i].get('SubmissionTime', 'N/A')
                item['customer_review'] = batch_results[i].get('ReviewText', 'N/A')
                item['customer_support'] = batch_results[i].get('TotalPositiveFeedbackCount', 'N/A')
                item['customer_disagree'] = batch_results[i].get('TotalNegativeFeedbackCount', 'N/A')

                yield item
            except Exception as e:
                print('Exception:', e)
                break

        if (offset_number + limit_number) < total_number:
            offset_number += limit_number
            next_page = re.sub(r'limit=\d+&offset=\d+', f'limit={30}&offset={offset_number}', response.url)
            yield Request(url=next_page, callback=self.review_parse, meta={'product_name': product_name})

