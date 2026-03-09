import tempfile
import pandas as pd
from fastapi.responses import FileResponse

def build_rows(shipment, items):
    rows = []

    for i, item in enumerate(items, start=1):
        qty = item.qty if item.qty is not None else ""
        unit_price = item.unit_price if item.unit_price is not None else ""
        gross_weight = item.gross_weight if item.gross_weight is not None else ""
        net_weight = item.net_weight if item.net_weight is not None else ""

        if item.value is not None:
            line_value = item.value
        elif item.qty is not None and item.unit_price is not None:
            line_value = item.qty * item.unit_price
        else:
            line_value = ""

        rows.append({
            "LineNumber": i,
            "ProductCode": item.article_no or "",
            "HTS": item.hs_code or "",
            "HTSDescription": item.description or "",
            "HTSDescriptionArabic": item.arabic_description or "",
            "CountryOfOrigin": item.origin or "",
            "CountryOfExport": shipment.country_of_export or "AE",
            "Quantity": qty,
            "QuantityUOM": item.uom or "PCS",
            "GrossWeight": gross_weight,
            "GrossWeightUOM": "KG",
            "NetWeight": net_weight,
            "NetWeightUOM": "KG",
            "UnitPrice": unit_price,
            "LineValueHS": line_value,
            "LineValueHSCurrency": shipment.currency or "AED",
            "ProductGroup": item.product_group or "",
            "InvoiceNumber": shipment.invoice_number or "",
            "InvoiceDate": shipment.invoice_date or "",
            "ShipmentID": shipment.id,
            "SourcePage": item.source_page or "",
        })

    return rows

def export_excel(shipment, items):
    rows = build_rows(shipment, items)
    df = pd.DataFrame(rows)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(temp_file.name, index=False)

    return FileResponse(
        path=temp_file.name,
        filename=f"shipment_{shipment.id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

def export_combined(shipment, items):
    rows = build_rows(shipment, items)
    items_df = pd.DataFrame(rows)

    summary_df = pd.DataFrame([{
        "ShipmentID": shipment.id,
        "ShipmentNumber": shipment.shipment_number or "",
        "InvoiceNumber": shipment.invoice_number or "",
        "InvoiceDate": shipment.invoice_date or "",
        "Seller": shipment.seller_name or "",
        "Buyer": shipment.buyer_name or "",
        "Currency": shipment.currency or "AED",
        "CountryOfExport": shipment.country_of_export or "AE",
        "CountryOfImport": shipment.country_of_import or "",
        "TotalItems": len(items),
        "TotalValue": sum([x["LineValueHS"] for x in rows if isinstance(x["LineValueHS"], (int, float))]),
        "TotalGrossWeight": sum([x["GrossWeight"] for x in rows if isinstance(x["GrossWeight"], (int, float))]),
    }])

    totals_df = pd.DataFrame([{
        "TotalLines": len(items),
        "TotalQuantity": sum([x["Quantity"] for x in rows if isinstance(x["Quantity"], (int, float))]),
        "TotalGrossWeight": sum([x["GrossWeight"] for x in rows if isinstance(x["GrossWeight"], (int, float))]),
        "TotalNetWeight": sum([x["NetWeight"] for x in rows if isinstance(x["NetWeight"], (int, float))]),
        "TotalLineValue": sum([x["LineValueHS"] for x in rows if isinstance(x["LineValueHS"], (int, float))]),
        "Currency": shipment.currency or "AED",
    }])

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")

    with pd.ExcelWriter(temp_file.name, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        items_df.to_excel(writer, sheet_name="Items", index=False)
        totals_df.to_excel(writer, sheet_name="Totals", index=False)

    return FileResponse(
        path=temp_file.name,
        filename=f"shipment_{shipment.id}_combined.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

def export_saudi_format(shipment, items):
    rows = []

    for i, item in enumerate(items, start=1):
        qty = item.qty if item.qty is not None else ""
        unit_price = item.unit_price if item.unit_price is not None else ""
        gross_weight = item.gross_weight if item.gross_weight is not None else ""
        net_weight = item.net_weight if item.net_weight is not None else ""

        if item.value is not None:
            line_value = item.value
        elif item.qty is not None and item.unit_price is not None:
            line_value = item.qty * item.unit_price
        else:
            line_value = ""

        rows.append({
            "LineNumber": i,
            "HTS": item.hs_code or "",
            "HTSDescription": item.description or "",
            "HTSDescriptionArabic": item.arabic_description or "",
            "CountryOfOrigin": item.origin or "",
            "Quantity": qty,
            "QuantityUOM": item.uom or "PCS",
            "GrossWeight": gross_weight,
            "GrossWeightUOM": "KG",
            "NetWeight": net_weight,
            "NetWeightUOM": "KG",
            "UnitPrice": unit_price,
            "LineValueHS": line_value,
            "LineValueHSCurrency": shipment.currency or "AED",
            "ProductCode": item.article_no or "",
            "ProductGroup": item.product_group or "",
            "InvoiceNumber": shipment.invoice_number or "",
            "InvoiceDate": shipment.invoice_date or "",
            "ShipmentID": shipment.id,
            "SourcePage": item.source_page or "",
        })

    df = pd.DataFrame(rows)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(temp_file.name, index=False)

    return FileResponse(
        path=temp_file.name,
        filename=f"shipment_{shipment.id}_saudi.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
