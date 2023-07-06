# BA024webscraping_Diy.com
This project is a common website that uses Ajax technology to load its customer reviews dynamically.
As usual, apply search words to find all pages of the specific brand's products. And extract the product detailed link from each page.
Next, find the Ajax website link of customer reviews from the detailed product link, then extract customer reviews from the Ajax link.
The detail can be summarized as follows.
1. Use search words to find the product pages.
2. In each product page, extract each product's link.
3. In the product's link, find the customer reviews' link which is loaded through the Ajax URL.
4. Then, replace the product_id, offset number and limit number of each Ajax URL that is related to different products to extract the customer revies.
TIP: Ajax URL uses json format data.
