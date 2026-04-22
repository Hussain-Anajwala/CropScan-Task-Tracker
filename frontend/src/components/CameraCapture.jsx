import { useEffect, useRef, useState } from "react";
import useCamera from "../hooks/useCamera";

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.split(",")[1] || "");
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function CameraCapture({ onImageChange }) {
  const { videoRef, stream, error, startCamera, stopCamera } = useCamera();
  const canvasRef = useRef(null);
  const [mode, setMode] = useState("upload");
  const [preview, setPreview] = useState("");

  useEffect(() => () => {
    if (preview.startsWith("blob:")) {
      URL.revokeObjectURL(preview);
    }
  }, [preview]);

  async function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const objectUrl = URL.createObjectURL(file);
    const advisoryImageBase64 = await fileToBase64(file);
    setPreview(objectUrl);
    onImageChange({
      file,
      previewUrl: objectUrl,
      advisoryImageBase64,
    });
  }

  async function handleCapture() {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/png");
    setPreview(dataUrl);
    const response = await fetch(dataUrl);
    const blob = await response.blob();
    const file = new File([blob], "capture.png", { type: "image/png" });
    onImageChange({
      file,
      previewUrl: dataUrl,
      advisoryImageBase64: dataUrl.split(",")[1],
    });
  }

  return (
    <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-stone-200">
      <div className="flex gap-3">
        <button
          className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === "upload" ? "bg-cropscan-leaf text-white" : "bg-stone-100"}`}
          onClick={() => {
            setMode("upload");
            stopCamera();
          }}
          type="button"
        >
          File Upload
        </button>
        <button
          className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === "camera" ? "bg-cropscan-leaf text-white" : "bg-stone-100"}`}
          onClick={() => {
            setMode("camera");
            startCamera();
          }}
          type="button"
        >
          Camera
        </button>
      </div>

      {mode === "upload" ? (
        <label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-10 text-center">
          <span className="text-sm font-medium text-stone-700">Choose a leaf image</span>
          <input className="hidden" type="file" accept="image/*" onChange={handleFileChange} />
        </label>
      ) : (
        <div className="mt-5 space-y-3">
          <video ref={videoRef} autoPlay playsInline className="w-full rounded-2xl bg-stone-200" />
          <button className="rounded-full bg-amber-500 px-4 py-2 font-semibold text-white" onClick={handleCapture} type="button">
            Capture Leaf
          </button>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
        </div>
      )}

      {preview ? <img alt="Selected leaf preview" className="mt-5 w-full rounded-2xl object-cover" src={preview} /> : null}
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
