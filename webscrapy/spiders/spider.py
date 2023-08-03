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
    allowed_domains = ["www.diy.com", "api.bazaarvoice.com", "api.kingfisher.com"]
    headers = {}  #

    def start_requests(self):
        # keywords = ['dewalt', 'Stanley', 'Black+Decker', 'Craftsman', 'Porter-Cable', 'Bostitch', 'Facom', 'MAC Tools', 'Vidmar', 'Lista', 'Irwin Tools', 'Lenox', 'Proto', 'CribMaster', 'Powers Fasteners', 'cub-cadet', 'hustler', 'troy-bilt', 'rover', 'BigDog Mower', 'MTD']
        exist_keywords = ['dewalt', 'stanley tools', 'Black+Decker', 'Bostitch', 'Facom', 'Irwin', 'Lenox'] # ***************************************
        # company = 'Stanley Black and Decker'
        # exist_keywords = ['dewalt']

        # from search words to generate product_urls
        for keyword in exist_keywords:
            push_key = {'keyword': keyword}
            search_url = f'https://www.diy.com/search?term={keyword}'

            yield Request(
                url=search_url,
                callback=self.parse,
                cb_kwargs=push_key,
            )

    def parse(self, response, **kwargs):
        # extract the total number of product results
        page_number = int(re.search(r'"totalResults":(\d+)', response.body.decode('utf-8')).group(1))
        pages = (page_number // 24) + 1

        # Based on pages to build product_urls
        keyword = kwargs['keyword']
        product_urls = [f'https://www.diy.com/search?page={page}&term={keyword}' for page
                        in range(1, pages+1)]  # pages+1 ***************************************************************

        for product_url in product_urls:
            yield Request(url=product_url, callback=self.product_parse, meta={'product_brand': keyword})

    def product_parse(self, response: Request, **kwargs):
        product_brand = response.meta['product_brand']
        # extract the product url link from each page of product list
        product_urls = re.findall(r'"shareableUrl":"(.*?)"', response.body.decode('utf-8'))
        for product_url in product_urls:
            product_detailed_url = product_url.encode().decode('unicode-escape')

            yield Request(url=product_detailed_url, callback=self.product_detailed_parse, meta={'product_brand': product_brand})

    def product_detailed_parse(self, response, **kwargs):
        product_brand = response.meta['product_brand']
        product_id = response.xpath('.//*[@id="product-details"]//td[@data-test-id="product-ean-spec"]/text()')[
            0].extract()
        product_name = response.xpath('//h1[@id="product-title"]/text()')[0].extract()
        product_detail = response.xpath('//tbody/tr')

        # extract product detail infor
        product_type = 'N/A'
        product_model = 'N/A'

        for product in product_detail:
            th_text = product.xpath('./th/text()')[0].extract()
            td_text = product.xpath('./td/text()').extract()
            if th_text == "Product type":
                product_type = td_text[0] if td_text else 'N/A'
            elif th_text == 'Product brand':
                product_brand = td_text[0] if td_text else 'N/A'
            elif th_text == "Model name/number":
                product_model = td_text[0] if td_text else 'N/A'


        # Product reviews url
        product_detailed_href = f'https://api.bazaarvoice.com/data/reviews.json?resource=reviews&action' \
                                f'=REVIEWS_N_STATS&filter=productid%3Aeq%3A{product_id}&filter=contentlocale%3Aeq%3Aen_FR%2Cfr_FR' \
                                f'%2Cen_US%2Cen_GB%2Cen_GB&filter=isratingsonly%3Aeq%3Afalse&filter_reviews' \
                                f'=contentlocale%3Aeq%3Aen_FR%2Cfr_FR%2Cen_US%2Cen_GB%2Cen_GB&include=authors' \
                                f'%2Cproducts&filteredstats=reviews&Stats=Reviews&limit=8&offset=0&sort' \
                                f'=submissiontime%3Adesc&passkey=7db2nllxwguwj2eu7fxvvgm0t&apiversion=5.5&displaycode' \
                                f'=2191-en_gb '

        if product_detailed_href:
            yield Request(url=product_detailed_href, callback=self.review_parse, meta={'product_name': product_name, 'product_model':product_model, 'product_brand':product_brand, 'product_type':product_type})

    def review_parse(self, response: Request, **kwargs):
        product_name = response.meta['product_name']
        product_brand = response.meta['product_brand']
        product_model = response.meta['product_model']
        product_type = response.meta['product_type']

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

        for i in range(limit_number):
            item = WebscrapyItem()
            # results = batch_results.get(result_key, {}).get('Results', [])

            try:
                item['review_id'] = batch_results[i].get('Id', 'N/A')
                item['product_website'] = 'diy_en'
                item['product_type'] = product_type
                item['product_name'] = product_name
                item['product_brand'] = product_brand
                item['product_model'] = product_model
                item['customer_name'] = batch_results[i].get('UserNickname', 'Anonymous') if batch_results[i].get('UserNickname', 'Anonymous') else 'Ananymous'
                item['customer_rating'] = batch_results[i].get('Rating', 'N/A')
                item['customer_date'] = batch_results[i].get('SubmissionTime', 'N/A')
                item['customer_review'] = batch_results[i].get('ReviewText', 'N/A')
                item['customer_support'] = batch_results[i].get('TotalPositiveFeedbackCount', 'N/A')
                item['customer_disagree'] = batch_results[i].get('TotalNegativeFeedbackCount', 'N/A')

                yield item
            except Exception as e:
                break

        if (offset_number + limit_number) < total_number:
            offset_number += limit_number
            next_page = re.sub(r'limit=\d+&offset=\d+', f'limit={30}&offset={offset_number}', response.url)
            yield Request(url=next_page, callback=self.review_parse, meta={'product_name': product_name, 'product_model':product_model, 'product_brand':product_brand, 'product_type':product_type})

