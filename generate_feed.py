import os
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom


SHOPIFY_STORE = "it3u3i-5e.myshopify.com"
ACCESS_TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]


API_VERSION = "2025-01"
URL = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/products.json"


headers = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}


root = ET.Element("Products")


params = {
    "limit": 250,
    "status": "active"
}


products = []


while True:
    response = requests.get(URL, headers=headers, params=params)
    response.raise_for_status()


    data = response.json()
    products.extend(data.get("products", []))


    link_header = response.headers.get("Link", "")


    if 'rel="next"' not in link_header:
        break


    next_url = None


    for link in link_header.split(","):
        if 'rel="next"' in link:
            next_url = link.split(";")[0].strip().strip("<>")
            break


    if not next_url:
        break


    URL = next_url
    params = {}


for product in products:


    for variant in product.get("variants", []):


        offer = ET.SubElement(root, "Offer")


        def add_field(name, value):
            element = ET.SubElement(offer, name)
            element.text = str(value or "")
            return element


        title = product.get("title", "")
        vendor = product.get("vendor", "")


        description = product.get("body_html", "")
        description = description.replace("<", " ").replace(">", " ")


        price = variant.get("price", "0")
        sku = variant.get("sku") or str(variant.get("id"))


        handle = product.get("handle", "")
        product_url = f"https://saivera.net/products/{handle}"


        inventory_quantity = variant.get("inventory_quantity", 0)


        stock = "disponibile" if inventory_quantity > 0 else "non disponibile"


        image = ""


        if variant.get("image_id"):
            for product_image in product.get("images", []):
                if product_image.get("id") == variant.get("image_id"):
                    image = product_image.get("src", "")
                    break


        if not image and product.get("images"):
            image = product["images"][0].get("src", "")


        add_field("Name", title)
        add_field("Brand", vendor)
        add_field("Description", description)
        add_field("Price", price)
        add_field("Code", sku)
        add_field("Link", product_url)
        add_field("Stock", stock)
        add_field("Categories", "Software")
        add_field("Image", image)
        add_field("ShippingCost", "0")


xml_string = ET.tostring(root, encoding="utf-8")


pretty_xml = minidom.parseString(xml_string).toprettyxml(
    indent="  ",
    encoding="UTF-8"
)


with open("trovaprezzi.xml", "wb") as file:
    file.write(pretty_xml)


print(f"Feed generated successfully with {len(products)} products.")
