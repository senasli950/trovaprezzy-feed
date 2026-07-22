import os
import re
import html
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom




# =========================
# SHOPIFY CONFIGURATION
# =========================


SHOPIFY_STORE = "it3u3i-5e.myshopify.com"
ACCESS_TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]


API_VERSION = "2025-01"


URL = (
    f"https://{SHOPIFY_STORE}"
    f"/admin/api/{API_VERSION}/graphql.json"
)


HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}




# =========================
# BRAND RULES
# =========================


BRAND_RULES = [


    # Microsoft products
    ("xbox game pass", "Microsoft"),
    ("microsoft office", "Microsoft"),
    ("office 365", "Microsoft"),
    ("office 2024", "Microsoft"),
    ("office 2021", "Microsoft"),
    ("office 2019", "Microsoft"),
    ("office 2016", "Microsoft"),
    ("office 2013", "Microsoft"),
    ("windows server", "Microsoft"),
    ("windows 11", "Microsoft"),
    ("windows 10", "Microsoft"),
    ("windows 7", "Microsoft"),
    ("windows 8", "Microsoft"),
    ("windows", "Microsoft"),
    ("minecraft", "Microsoft"),


    # Antivirus and VPN
    ("kaspersky", "Kaspersky"),
    ("norton", "Norton"),
    ("mcafee", "McAfee"),
    ("avast", "Avast"),
    ("avg", "AVG"),
    ("bitdefender", "Bitdefender"),
    ("eset", "ESET"),
    ("surfshark", "Surfshark"),
    ("nordvpn", "NordVPN"),
    ("cyberghost", "CyberGhost"),
    ("expressvpn", "ExpressVPN"),


    # Software
    ("adobe", "Adobe"),
    ("photoshop", "Adobe"),
    ("acrobat", "Adobe"),
    ("autodesk", "Autodesk"),
    ("autocad", "Autodesk"),
    ("coreldraw", "Corel"),


    # Subscriptions
    ("youtube premium", "Google"),
    ("google one", "Google"),


    # Games and publishers
    ("ea sports fc", "Electronic Arts"),
    ("fifa", "Electronic Arts"),
    ("resident evil", "Capcom"),
    ("nioh", "Koei Tecmo"),
    ("crimson desert", "Pearl Abyss"),
    ("arc raiders", "Embark Studios"),
    ("007: first light", "IO Interactive"),
]




# =========================
# GRAPHQL QUERY
# =========================


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




# =========================
# BRAND DETECTION
# =========================


def detect_brand(title, vendor):


    title_lower = title.lower()


    # More specific rules are checked first
    for keyword, brand in BRAND_RULES:


        if keyword in title_lower:
            return brand


    # If no rule matches, use Shopify Vendor
    if vendor and vendor.strip():


        return vendor.strip()


    # Final fallback
    return "SAIVERA"




# =========================
# DESCRIPTION CLEANING
# =========================


def clean_description(description):


    if not description:
        return ""


    description = html.unescape(description)


    description = re.sub(
        r"<[^>]+>",
        " ",
        description
    )


    description = re.sub(
        r"\s+",
        " ",
        description
    )


    return description.strip()




# =========================
# CATEGORY
# =========================


def get_category(product):


    category = product.get("category")


    if not category:


        return "Computer Software"


    full_name = category.get("fullName")


    name = category.get("name")


    if full_name:


        # Example:
        #
        # Network Software in Computer Software
        #
        # Becomes:
        #
        # Computer Software > Network Software


        if " in " in full_name:


            parts = full_name.split(" in ")


            parts.reverse()


            return " > ".join(
                part.strip()
                for part in parts
            )


        return full_name


    return name or "Computer Software"




# =========================
# GET ACTIVE PRODUCTS
# =========================


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


            raise Exception(
                data["errors"]
            )


        product_data = (
            data["data"]["products"]
        )


        products.extend(
            product_data["nodes"]
        )


        page_info = (
            product_data["pageInfo"]
        )


        if not page_info["hasNextPage"]:


            break


        cursor = (
            page_info["endCursor"]
        )


    return products




# =========================
# XML FIELD
# =========================


def add_field(parent, name, value):


    element = ET.SubElement(
        parent,
        name
    )


    element.text = str(
        value or ""
    )


    return element




# =========================
# GENERATE FEED
# =========================


def generate_feed():


    products = get_products()


    root = ET.Element(
        "Products"
    )


    total_offers = 0


    for product in products:


        title = product.get(
            "title",
            ""
        )


        handle = product.get(
            "handle",
            ""
        )


        vendor = product.get(
            "vendor",
            ""
        )


        description = clean_description(


            product.get(
                "descriptionHtml",
                ""
            )


        )


        brand = detect_brand(
            title,
            vendor
        )


        category = get_category(
            product
        )


        product_url = (


            "https://saivera.net/products/"
            + handle


        )


        images = (
            product
            .get("images", {})
            .get("nodes", [])
        )


        default_image = ""


        if images:


            default_image = (


                images[0]
                .get("url", "")


            )


        variants = (


            product
            .get("variants", {})
            .get("nodes", [])


        )


        for variant in variants:


            offer = ET.SubElement(


                root,


                "Offer"


            )


            sku = variant.get(
                "sku"
            )


            if not sku:


                sku = title


            price = variant.get(
                "price",
                "0"
            )


            image = default_image


            variant_image = (


                variant.get(
                    "image"
                )


            )


            if variant_image:


                image = (


                    variant_image
                    .get("url", "")


                )


            add_field(


                offer,


                "Name",


                title


            )


            add_field(


                offer,


                "Brand",


                brand


            )


            add_field(


                offer,


                "Description",


                description


            )


            add_field(


                offer,


                "Price",


                price


            )


            add_field(


                offer,


                "Code",


                sku


            )


            add_field(


                offer,


                "Link",


                product_url


            )


            # All ACTIVE products are available
            add_field(


                offer,


                "Stock",


                "disponibile"


            )


            add_field(


                offer,


                "Categories",


                category


            )


            add_field(


                offer,


                "Image",


                image


            )


            add_field(


                offer,


                "ShippingCost",


                "0"


            )


            total_offers += 1


    xml_string = ET.tostring(


        root,


        encoding="utf-8"


    )


    pretty_xml = (


        minidom


        .parseString(


            xml_string


        )


        .toprettyxml(


            indent="  ",


            encoding="UTF-8"


        )


    )


    with open(


        "trovaprezzi.xml",


        "wb"


    ) as file:


        file.write(


            pretty_xml


        )


    print(


        "Feed generated successfully."


    )


    print(


        f"Active products: {len(products)}"


    )


    print(


        f"Total offers: {total_offers}"


    )




if __name__ == "__main__":


    generate_feed()
