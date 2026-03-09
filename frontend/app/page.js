"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function Home() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [eta, setEta] = useState("");
  const [itemsCount, setItemsCount] = useState(0);
  const [error, setError] = useState("");

  const router = useRouter();

  const uploadFile = async () => {
    if (!file) {
      alert("Select a PDF first");
      return;
    }

    setUploading(true);
    setProgress(0);
    setStatus("Uploading file");
    setEta("Starting...");
    setItemsCount(0);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const uploadResponse = await axios.post(
        "http://127.0.0.1:8000/upload-with-progress",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const jobId = uploadResponse.data.job_id;

      const interval = setInterval(async () => {
        try {
          const statusResponse = await axios.get(
            `http://127.0.0.1:8000/job-status/${jobId}`
          );

          const job = statusResponse.data;

          if (job.error) {
            clearInterval(interval);
            setUploading(false);
            setError(job.error);
            return;
          }

          setProgress(job.progress || 0);
          setStatus(job.status || "");
          setEta(job.eta || "");
          setItemsCount(job.items_count || 0);

          if (job.done) {
            clearInterval(interval);
            setUploading(false);

            if (job.shipment_id) {
              setTimeout(() => {
                router.push(`/shipments/${job.shipment_id}`);
              }, 1000);
            } else {
              setError("Processing finished but no shipment was created.");
            }
          }
        } catch (pollError) {
          clearInterval(interval);
          setUploading(false);
          setError("Could not get progress status.");
          console.error(pollError);
        }
      }, 1000);
    } catch (err) {
      setUploading(false);
      setError("Upload failed.");
      console.error(err);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
      <div className="w-full max-w-2xl bg-slate-900 rounded-2xl shadow-xl p-8 border border-slate-800">
        <h1 className="text-3xl font-bold mb-2">Invoice Extractor</h1>
        <p className="text-slate-400 mb-8">
          Upload a commercial invoice PDF and extract shipment data into Excel.
        </p>

        <div className="mb-6">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4
                       file:rounded-lg file:border-0 file:text-sm file:font-semibold
                       file:bg-purple-600 file:text-white hover:file:bg-purple-500"
          />
        </div>

        <button
          onClick={uploadFile}
          disabled={uploading}
          className={`px-5 py-3 rounded-lg font-semibold transition ${
            uploading
              ? "bg-slate-700 text-slate-300 cursor-not-allowed"
              : "bg-purple-600 hover:bg-purple-500 text-white"
          }`}
        >
          {uploading ? "Processing..." : "Upload Invoice"}
        </button>

        {uploading || progress > 0 ? (
          <div className="mt-8">
            <div className="flex justify-between mb-2 text-sm text-slate-300">
              <span>{status || "Processing..."}</span>
              <span>{progress}%</span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-4 overflow-hidden">
              <div
                className="bg-green-500 h-4 transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <div className="mt-4 text-sm text-slate-400 space-y-1">
              <p>
                <strong className="text-slate-200">Estimated time:</strong> {eta || "Estimating..."}
              </p>
              <p>
                <strong className="text-slate-200">Current file:</strong> {file?.name || "-"}
              </p>
              <p>
                <strong className="text-slate-200">Extracted items:</strong> {itemsCount}
              </p>
            </div>
          </div>
        ) : null}

        {error ? (
          <div className="mt-6 rounded-lg bg-red-900/40 border border-red-700 p-4 text-red-300">
            {error}
          </div>
        ) : null}

        {!uploading && progress === 100 && !error ? (
          <div className="mt-6 rounded-lg bg-green-900/30 border border-green-700 p-4 text-green-300">
            Processing completed. Redirecting to shipment details...
          </div>
        ) : null}
      </div>
    </main>
  );
}