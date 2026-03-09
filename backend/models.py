from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_number = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(String, nullable=True)
    seller_name = Column(String, nullable=True)
    buyer_name = Column(String, nullable=True)
    total_value = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    total_weight = Column(Float, nullable=True)
    country_of_export = Column(String, nullable=True)
    country_of_import = Column(String, nullable=True)
    file_name = Column(String, nullable=True)

    items = relationship("LineItem", back_populates="shipment", cascade="all, delete")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    article_no = Column(String, nullable=True)
    hs_code = Column(String, nullable=True)
    description = Column(String, nullable=True)
    arabic_description = Column(String, nullable=True)
    qty = Column(Float, nullable=True)
    uom = Column(String, nullable=True)
    unit_price = Column(Float, nullable=True)
    value = Column(Float, nullable=True)
    gross_weight = Column(Float, nullable=True)
    net_weight = Column(Float, nullable=True)
    origin = Column(String, nullable=True)
    product_group = Column(String, nullable=True)
    source_page = Column(Integer, nullable=True)

    shipment = relationship("Shipment", back_populates="items")
