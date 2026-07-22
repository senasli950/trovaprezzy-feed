import os
import re
import html
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom


SHOPIFY_STORE = "it3u3i-5e.myshopify.com"
ACCESS_TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]


API_VERSION = "2025-01"
URL = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/graphql.json"


HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}


QUERY = """
query GetProducts($cursor: String) {
  products(
    first: 100
    after: $cursor
    query: "status:ACTIVE"
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }


    nodes {
      title
      handle
      vendor
      descriptionHtml


      category {
        name
        fullName
      }


      images(first: 10) {
        nodes {
          url
        }
      }


      variants(first: 100) {
        nodes {
          sku
          price
          image {
            url
          }
        }
      }
    }
  }
}
"""




def clean_description(description):
    if not description:
        return ""


    description = html.unescape(description)
    description = re.sub(r"<[^>]+>", " ", description)
    description = re.sub(r"\s+", " ", description)


    return description.strip()




def get_category(product):
    category = product.get("category")


    if not category:
        return "Computer Software"


    full_name = category.get("fullName")
    name = category.get("name")


    if full_name:
        # Shopify format:
        # "Network Software in Computer Software"
        if " in " in full_name:
            parts = full_name.split(" in ")


            # Reverse the order:
            # Network Software in Computer Software
            # becomes:
            # Computer Software > Network Software
            parts.reverse()


            return " > ".join(part.strip() for part in parts)


        return full_name


    return name or "Computer Software"




def get_products():
    products = []
    cursor = None


    while True:


        response = requests.post(
            URL,
            headers=HEADERS,
            json={
                "query": QUERY,
                "variables": {
                    "cursor": cursor
                }
            }
        )


        response.raise_for_status()


        data = response.json()


        if "errors" in data:
            raise Exception(data["errors"])


        product_data = data["data"]["products"]


        products.extend(product_data["nodes"])


        page_info = product_data["pageInfo"]


        if not page_info["hasNextPage"]:
            break


        cursor = page_info["endCursor"]


    return products




def add_field(parent, name, value):
    element = ET.SubElement(parent, name)
    element.text = str(value or "")
    return element




def generate_feed():


    products = get_products()


    root = ET.Element("Products")


    total_offers = 0


    for product in products:


        title = product.get("title", "")
        vendor = product.get("vendor", "")
        handle = product.get("handle", "")


        description = clean_description(
            product.get("descriptionHtml", "")
        )


        category = get_category(product)


        product_url = f"https://saivera.net/products/{handle}"


        images = product.get("images", {}).get("nodes", [])


        default_image = ""


        if images:
            default_image = images[0].get("url", "")


        variants = product.get("variants", {}).get("nodes", [])


        for variant in variants:


            offer = ET.SubElement(root, "Offer")


            sku = variant.get("sku")


            if not sku:
                sku = title


            image = default_image


            variant_image = variant.get("image")


            if variant_image:
                image = variant_image.get("url", "")


            price = variant.get("price", "0")


            add_field(offer, "Name", title)
            add_field(offer, "Brand", vendor)
            add_field(offer, "Description", description)
            add_field(offer, "Price", price)
            add_field(offer, "Code", sku)
            add_field(offer, "Link", product_url)


            # All ACTIVE products are considered available
            add_field(offer, "Stock", "disponibile")


            add_field(offer, "Categories", category)
            add_field(offer, "Image", image)
            add_field(offer, "ShippingCost", "0")


            total_offers += 1


    xml_string = ET.tostring(
        root,
        encoding="utf-8"
    )


    pretty_xml = minidom.parseString(
        xml_string
    ).toprettyxml(
        indent="  ",
        encoding="UTF-8"
    )


    with open(
        "trovaprezzi.xml",
        "wb"
    ) as file:


        file.write(pretty_xml)


    print(
        f"Feed generated successfully."
    )


    print(
        f"Active products: {len(products)}"
    )


    print(
        f"Total offers: {total_offers}"
    )




if __name__ == "__main__":
    generate_feed()
