import pdfplumber
import re

COUNTRY_CODE_MAP = {
    "CAMBODIA": "KH",
    "CHINA": "CN",
    "PAKISTAN": "PK",
    "VIETNAM": "VN",
    "EGYPT": "EG",
    "INDONESIA": "ID",
    "JORDAN": "JO",
    "THAILAND": "TH",
    "INDIA": "IN",
    "MYANMAR": "MM",
    "JAPAN": "JP",
    "GERMANY": "DE",
    "FRANCE": "FR",
    "SPAIN": "ES",
    "TURKEY": "TR",
    "NETHERLANDS": "NL",
    "UNITED KINGDOM": "GB",
    "UK": "GB",
    "GREAT BRITAIN": "GB",
    "UNITED STATES": "US",
    "USA": "US",
    "CANADA": "CA",
    "AUSTRALIA": "AU",
    "HONG KONG": "HK",
    "MALAYSIA": "MY",
    "SERBIA": "RS",
    "POLAND": "PL",
    "SLOVENIA": "SI",
    "ITALY": "IT",
}

def clean_text(value):
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()

def try_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return None

def normalize_country_code(country_name):
    if not country_name:
        return ""
    return COUNTRY_CODE_MAP.get(country_name.strip().upper(), country_name.strip().upper())

def parse_asics_tables(pdf):
    items = []

    shipment_info = {
        "invoice_number": None,
        "invoice_date": None,
        "seller_name": None,
        "buyer_name": None,
        "total_value": None,
        "currency": "AED",
        "total_weight": None,
        "country_of_export": "AE",
        "country_of_import": None,
    }

    for page_number, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        text_upper = text.upper()

        if not shipment_info["seller_name"] and "ASICS ARABIA FZE" in text_upper:
            shipment_info["seller_name"] = "ASICS ARABIA FZE"

        if not shipment_info["buyer_name"] and "Q EXPRESS DOCUMENT TRANSPORT LLC" in text_upper:
            shipment_info["buyer_name"] = "Q Express Document Transport LLC"

        if not shipment_info["invoice_number"]:
            match = re.search(r"Invoice\s+No[:\s]+(\d+)", text, re.IGNORECASE)
            if match:
                shipment_info["invoice_number"] = match.group(1)

        if not shipment_info["invoice_date"]:
            match = re.search(r"Invoice\s+Date[:\s]+([0-9/\-: ]+[APMapm]*)", text, re.IGNORECASE)
            if match:
                shipment_info["invoice_date"] = match.group(1).strip()

        tables = page.extract_tables()

        for table in tables:
            if not table or len(table) < 2:
                continue

            for row in table:
                row = [clean_text(x) for x in row]

                if len(row) < 15:
                    continue

                joined = " ".join(row).upper()

                skip_words = [
                    "PRODUCT DESCRIPTION",
                    "PRODUCT CODE",
                    "COUNTRY OF ORIGIN",
                    "AMOUNT (AED)",
                    "COMMERCIAL INVOICE",
                    "INVOICE NO",
                    "CUSTOMER",
                    "HTSDESCRIPTION",
                ]

                if any(word in joined for word in skip_words):
                    continue

                article_no = row[2]
                description = row[3]
                product_group = row[4]
                origin = row[5]
                hs_code = row[9]
                qty = row[10]
                unit_price = row[11]
                value = row[12]
                gross_weight = row[13]

                if not article_no and not description:
                    continue

                items.append({
                    "article_no": article_no,
                    "hs_code": hs_code,
                    "description": description,
                    "arabic_description": "",
                    "qty": try_float(qty),
                    "uom": "PCS",
                    "unit_price": try_float(unit_price),
                    "value": try_float(value),
                    "gross_weight": try_float(gross_weight),
                    "net_weight": try_float(gross_weight),
                    "origin": normalize_country_code(origin),
                    "product_group": product_group,
                    "source_page": page_number,
                })

    return shipment_info, items

def parse_amazon_tables(pdf):
    items = []

    shipment_info = {
        "invoice_number": None,
        "invoice_date": None,
        "seller_name": None,
        "buyer_name": None,
        "total_value": None,
        "currency": "AED",
        "total_weight": None,
        "country_of_export": "AE",
        "country_of_import": "SA",
    }

    for page_number, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""

        if not shipment_info["invoice_number"]:
            match = re.search(r"Invoice No\s*\n?([A-Z0-9\-_]+)", text, re.IGNORECASE)
            if match:
                shipment_info["invoice_number"] = match.group(1).strip()

        if not shipment_info["invoice_date"]:
            match = re.search(r"Date\s*\n?([0-9/]{6,20})", text, re.IGNORECASE)
            if match:
                shipment_info["invoice_date"] = match.group(1).strip()

        if not shipment_info["seller_name"]:
            shipment_info["seller_name"] = "Q Tech General Trading LLC"

        if not shipment_info["buyer_name"]:
            shipment_info["buyer_name"] = "Afaq Q Tech General Trading LLC"

        tables = page.extract_tables()

        for table in tables:
            if not table or len(table) == 0:
                continue

            for row in table:
                row = [clean_text(x) for x in row]

                if len(row) < 10:
                    continue

                joined = " ".join(row).upper()

                # Skip header row
                if "DESCRIPTION OF GOODS" in joined or "ACTUAL UNIT COST" in joined:
                    continue

                # Table format:
                # 0 PO
                # 1 ASIN
                # 2 DESCRIPTION OF GOODS
                # 3 HTS CODE SOURCE COUNTRY
                # 4 HTS CODE DESTINATION COUNTRY
                # 5 EXPORT CONTROL NUMBER
                # 6 COUNTRY OF ORIGIN
                # 7 QUANTITY SHIPPED
                # 8 ACTUAL UNIT COST
                # 9 TOTAL UNIT COST

                article_no = row[0]
                asin = row[1]
                description = row[2]
                hs_code = row[3]
                origin = row[6]
                qty = row[7]
                unit_price = row[8]
                value = row[9]

                if not article_no and not description:
                    continue

                items.append({
                    "article_no": article_no,
                    "hs_code": hs_code,
                    "description": description,
                    "arabic_description": "",
                    "qty": try_float(qty),
                    "uom": "PCS",
                    "unit_price": try_float(unit_price),
                    "value": try_float(value),
                    "gross_weight": None,
                    "net_weight": None,
                    "origin": normalize_country_code(origin),
                    "product_group": "",
                    "source_page": page_number,
                })

    return shipment_info, items

def extract_invoice_data(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = (pdf.pages[0].extract_text() or "").upper()

        if "PO ASIN DESCRIPTION OF GOODS" in first_page_text:
            return parse_amazon_tables(pdf)

        if "PRODUCT DESCRIPTION" in first_page_text and "PRODUCT CODE" in first_page_text:
            return parse_asics_tables(pdf)

        shipment_info, items = parse_amazon_tables(pdf)
        if items:
            return shipment_info, items

        return parse_asics_tables(pdf)
