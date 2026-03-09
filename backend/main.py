import os
import uuid
import threading
import time

from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import Shipment, LineItem
from extractor import extract_invoice_data
from exports import (
    export_excel as generate_excel_file,
    export_combined as generate_combined_file,
    export_saudi_format as generate_saudi_file
)

# Create DB tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://super-duper-broccoli-8cmi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload folder
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory job tracker
jobs = {}


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def process_invoice_job(job_id, file_path, file_name):
    db = SessionLocal()

    try:
        jobs[job_id] = {
            "progress": 5,
            "status": "Starting processing",
            "eta": "Preparing file...",
            "done": False,
            "shipment_id": None,
            "file_name": file_name,
            "items_count": 0
        }

        time.sleep(0.5)

        jobs[job_id]["progress"] = 20
        jobs[job_id]["status"] = "Reading PDF pages"
        jobs[job_id]["eta"] = "Usually under 30 seconds"

        shipment_info, items = extract_invoice_data(file_path)

        jobs[job_id]["progress"] = 55
        jobs[job_id]["status"] = "Extracting line items"
        jobs[job_id]["eta"] = "Finalizing extracted data..."
        jobs[job_id]["items_count"] = len(items)

        shipment = Shipment(
            shipment_number=os.path.splitext(file_name)[0],
            invoice_number=shipment_info.get("invoice_number"),
            invoice_date=shipment_info.get("invoice_date"),
            seller_name=shipment_info.get("seller_name"),
            buyer_name=shipment_info.get("buyer_name"),
            total_value=shipment_info.get("total_value"),
            currency=shipment_info.get("currency"),
            total_weight=shipment_info.get("total_weight"),
            country_of_export=shipment_info.get("country_of_export"),
            country_of_import=shipment_info.get("country_of_import"),
            file_name=file_name,
        )

        jobs[job_id]["progress"] = 70
        jobs[job_id]["status"] = "Saving shipment details"
        jobs[job_id]["eta"] = "Almost done"

        db.add(shipment)
        db.commit()
        db.refresh(shipment)

        for item in items:
            db_item = LineItem(
                shipment_id=shipment.id,
                article_no=item.get("article_no"),
                hs_code=item.get("hs_code"),
                description=item.get("description"),
                arabic_description=item.get("arabic_description"),
                qty=item.get("qty"),
                uom=item.get("uom"),
                unit_price=item.get("unit_price"),
                value=item.get("value"),
                gross_weight=item.get("gross_weight"),
                net_weight=item.get("net_weight"),
                origin=item.get("origin"),
                product_group=item.get("product_group"),
                source_page=item.get("source_page"),
            )
            db.add(db_item)

        db.commit()

        jobs[job_id]["progress"] = 90
        jobs[job_id]["status"] = "Preparing Excel exports"
        jobs[job_id]["eta"] = "A few more seconds"
        jobs[job_id]["shipment_id"] = shipment.id

        time.sleep(1)

        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "Completed"
        jobs[job_id]["eta"] = "Ready"
        jobs[job_id]["done"] = True
        jobs[job_id]["shipment_id"] = shipment.id
        jobs[job_id]["items_count"] = len(items)

    except Exception as e:
        jobs[job_id] = {
            "progress": 100,
            "status": f"Error: {str(e)}",
            "eta": "Failed",
            "done": True,
            "shipment_id": None,
            "file_name": file_name,
            "items_count": 0
        }
    finally:
        db.close()


# Home route
@app.get("/")
def home():
    return {"message": "Invoice Extractor API running"}


# Original upload route
@app.post("/upload")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    shipment_info, items = extract_invoice_data(file_path)

    shipment = Shipment(
        shipment_number=os.path.splitext(file.filename)[0],
        invoice_number=shipment_info.get("invoice_number"),
        invoice_date=shipment_info.get("invoice_date"),
        seller_name=shipment_info.get("seller_name"),
        buyer_name=shipment_info.get("buyer_name"),
        total_value=shipment_info.get("total_value"),
        currency=shipment_info.get("currency"),
        total_weight=shipment_info.get("total_weight"),
        country_of_export=shipment_info.get("country_of_export"),
        country_of_import=shipment_info.get("country_of_import"),
        file_name=file.filename,
    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    for item in items:
        db_item = LineItem(
            shipment_id=shipment.id,
            article_no=item.get("article_no"),
            hs_code=item.get("hs_code"),
            description=item.get("description"),
            arabic_description=item.get("arabic_description"),
            qty=item.get("qty"),
            uom=item.get("uom"),
            unit_price=item.get("unit_price"),
            value=item.get("value"),
            gross_weight=item.get("gross_weight"),
            net_weight=item.get("net_weight"),
            origin=item.get("origin"),
            product_group=item.get("product_group"),
            source_page=item.get("source_page"),
        )
        db.add(db_item)

    db.commit()

    return {
        "shipment_id": shipment.id,
        "file_name": file.filename,
        "items_count": len(items)
    }


# New upload route with progress tracking
@app.post("/upload-with-progress")
async def upload_with_progress(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    jobs[job_id] = {
        "progress": 0,
        "status": "Upload received",
        "eta": "Starting...",
        "done": False,
        "shipment_id": None,
        "file_name": file.filename,
        "items_count": 0
    }

    thread = threading.Thread(
        target=process_invoice_job,
        args=(job_id, file_path, file.filename),
        daemon=True
    )
    thread.start()

    return {
        "job_id": job_id,
        "file_name": file.filename
    }


# Get job progress
@app.get("/job-status/{job_id}")
def get_job_status(job_id: str):
    job = jobs.get(job_id)

    if not job:
        return {"error": "Job not found"}

    return job


# List all shipments
@app.get("/shipments")
def list_shipments(db: Session = Depends(get_db)):
    shipments = db.query(Shipment).all()

    results = []
    for s in shipments:
        results.append({
            "id": s.id,
            "shipment_number": s.shipment_number,
            "invoice_number": s.invoice_number,
            "invoice_date": s.invoice_date,
            "seller_name": s.seller_name,
            "buyer_name": s.buyer_name,
            "total_value": s.total_value,
            "currency": s.currency,
            "total_weight": s.total_weight,
            "country_of_export": s.country_of_export,
            "country_of_import": s.country_of_import,
            "file_name": s.file_name,
        })

    return results


# Get one shipment with items
@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()

    if not shipment:
        return {"error": "Shipment not found"}

    items = db.query(LineItem).filter(LineItem.shipment_id == shipment_id).all()

    shipment_data = {
        "id": shipment.id,
        "shipment_number": shipment.shipment_number,
        "invoice_number": shipment.invoice_number,
        "invoice_date": shipment.invoice_date,
        "seller_name": shipment.seller_name,
        "buyer_name": shipment.buyer_name,
        "total_value": shipment.total_value,
        "currency": shipment.currency,
        "total_weight": shipment.total_weight,
        "country_of_export": shipment.country_of_export,
        "country_of_import": shipment.country_of_import,
        "file_name": shipment.file_name,
    }

    items_data = []
    for item in items:
        items_data.append({
            "id": item.id,
            "shipment_id": item.shipment_id,
            "article_no": item.article_no,
            "hs_code": item.hs_code,
            "description": item.description,
            "arabic_description": item.arabic_description,
            "qty": item.qty,
            "uom": item.uom,
            "unit_price": item.unit_price,
            "value": item.value,
            "gross_weight": item.gross_weight,
            "net_weight": item.net_weight,
            "origin": item.origin,
            "product_group": item.product_group,
            "source_page": item.source_page,
        })

    return {
        "shipment": shipment_data,
        "items": items_data
    }


# Export Excel
@app.get("/shipments/{shipment_id}/export/excel")
def export_excel_route(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()

    if not shipment:
        return {"error": "Shipment not found"}

    items = db.query(LineItem).filter(LineItem.shipment_id == shipment_id).all()

    return generate_excel_file(shipment, items)


# Export Combined
@app.get("/shipments/{shipment_id}/export/combined")
def export_combined_route(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()

    if not shipment:
        return {"error": "Shipment not found"}

    items = db.query(LineItem).filter(LineItem.shipment_id == shipment_id).all()

    return generate_combined_file(shipment, items)


# Export Saudi Format
@app.get("/shipments/{shipment_id}/export/saudi")
def export_saudi_route(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()

    if not shipment:
        return {"error": "Shipment not found"}

    items = db.query(LineItem).filter(LineItem.shipment_id == shipment_id).all()

    return generate_saudi_file(shipment, items)
