import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re, sys

baseurl = "https://mamaearth.in/" 
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0 Chrome/89.0.4389.82'}

cat_url = "https://mamaearth.in/product-category/beauty"

page_req = requests.get(cat_url,headers=headers)
soup = BeautifulSoup(page_req.text, 'html.parser')

page_json = soup.find_all('script', type="application/json")[0].get_text()

page_json = json.loads(page_json)

nos_prodcuts = page_json["props"]["initialProps"]["pageProps"]["productCategorySchema"]["numberOfItems"]
products_json = page_json["props"]["initialProps"]["pageProps"]["productCategorySchema"]["itemListElement"]

# with open('content.html','w',encoding='utf8') as out:
#     out.write(page_req.text)

# with open('content.json','w',encoding='utf8') as out:
#     json.dump(products_json,out, indent=4, sort_keys=True, ensure_ascii=False)

products = pd.DataFrame()
reviews = pd.DataFrame()

for product in products_json:
    mpn = product['item']['mpn']
    name = product["item"]["name"]
    url = product["item"]["url"]

    product_page = requests.get(url,headers=headers)
    product_soup = BeautifulSoup(product_page.text, 'html.parser')
    product_json = product_soup.find_all('script', type="application/ld+json")[1].get_text()
    product_json = json.loads(product_json)

    rating = float(product_json["aggregateRating"]["ratingValue"])

    try:
        mrp = float(product_soup.find_all("tc", {"class": "slashed price"})[0].get_text()[1:].replace(',',''))
    except:
        mrp = float(product["item"]["offers"]["price"].replace(',',''))

    try:
        discount= float(product_soup.find_all("tc", {"class": "price__discount"})[0].get_text()[1:-1].split('%')[0])
    except:
        discount = 0.0
    
    data_dict = {
                "MPN": mpn,
                "Name": name,
                "Product Link": url,
                "Rating": rating,
                "MRP": mrp,
                "Discount": discount
    }

    products = products.append([data_dict])

    for rew in product['item']['review']:
        reviews = reviews.append([{
                        "MPN": int(mpn),
                        "Date": rew["datePublished"],
                        "User": rew["author"]["name"],
                        "Review Text":rew["reviewBody"]
        }])



products['Pack Size'] = products['Name'].str.extract(r'.* Pack of .*([0-9])',flags = re.IGNORECASE)
products["Pack Size"].fillna(1,inplace=True)
products['Pack Size'] = products['Pack Size'].astype(float)

products.to_csv("products.csv",index=False,columns=["MPN", "Name", "Product Link", "Rating", "MRP", "Pack Size", "Discount"])
reviews.to_csv("reviews.csv",index=False, columns=["MPN","Date","User","Review Text"])
