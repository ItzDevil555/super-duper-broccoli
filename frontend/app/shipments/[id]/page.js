"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

const API = "https://super-duper-broccoli-1.onrender.com";

export default function ShipmentDetails() {
  const params = useParams();
  const shipmentId = params?.id;

  const [shipmentData, setShipmentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!shipmentId) return;

    const fetchShipment = async () => {
      try {
        setLoading(true);

        const res = await fetch(`${API}/shipments/${shipmentId}`);

        if (!res.ok) {
          throw new Error(`Failed to fetch shipment: ${res.status}`);
        }

        const data = await res.json();
        console.log("Shipment API response:", data);
        setShipmentData(data);
      } catch (err) {
        console.error("Error fetching shipment:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchShipment();
  }, [shipmentId]);

  if (!shipmentId) {
    return (
      <div className="p-10 text-white bg-slate-950 min-h-screen">
        Loading shipment id...
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-10 text-white bg-slate-950 min-h-screen">
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-10 text-red-400 bg-slate-950 min-h-screen">
        Error: {error}
      </div>
    );
  }

  if (!shipmentData || !shipmentData.shipment || !shipmentData.items) {
    return (
      <div className="p-10 text-red-400 bg-slate-950 min-h-screen">
        Invalid shipment data
      </div>
    );
  }

  const { shipment, items } = shipmentData;

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-6">Shipment Details</h1>

      <div className="bg-slate-800 p-4 rounded mb-6">
        <p><strong>Shipment ID:</strong> {shipment.id}</p>
        <p><strong>File Name:</strong> {shipment.file_name}</p>
        <p><strong>Invoice Number:</strong> {shipment.invoice_number || "N/A"}</p>
        <p><strong>Seller:</strong> {shipment.seller_name || "N/A"}</p>
        <p><strong>Buyer:</strong> {shipment.buyer_name || "N/A"}</p>
        <p><strong>Total Items:</strong> {items.length}</p>
      </div>

      <div className="flex gap-4 mb-6 flex-wrap">
        <a
          href={`${API}/shipments/${shipment.id}/export/excel`}
          className="bg-green-600 px-4 py-2 rounded"
          target="_blank"
          rel="noreferrer"
        >
          Export Excel
        </a>

        <a
          href={`${API}/shipments/${shipment.id}/export/combined`}
          className="bg-blue-600 px-4 py-2 rounded"
          target="_blank"
          rel="noreferrer"
        >
          Export Combined
        </a>

        <a
          href={`${API}/shipments/${shipment.id}/export/saudi`}
          className="bg-yellow-500 px-4 py-2 rounded text-black"
          target="_blank"
          rel="noreferrer"
        >
          Export Saudi Format
        </a>
      </div>

      <div className="overflow-auto bg-slate-900 rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-700">
            <tr>
              <th className="p-2 text-left">Article No</th>
              <th className="p-2 text-left">Description</th>
              <th className="p-2 text-left">Qty</th>
              <th className="p-2 text-left">UOM</th>
              <th className="p-2 text-left">Unit Price</th>
              <th className="p-2 text-left">Origin</th>
              <th className="p-2 text-left">Product Group</th>
              <th className="p-2 text-left">Page</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b border-slate-700">
                <td className="p-2">{item.article_no}</td>
                <td className="p-2">{item.description}</td>
                <td className="p-2">{item.qty}</td>
                <td className="p-2">{item.uom}</td>
                <td className="p-2">{item.unit_price}</td>
                <td className="p-2">{item.origin}</td>
                <td className="p-2">{item.product_group}</td>
                <td className="p-2">{item.source_page}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}