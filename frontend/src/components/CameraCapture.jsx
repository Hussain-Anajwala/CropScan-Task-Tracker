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

export default function CameraCapture({ onImageChange, image, onReset }) {
  const { videoRef, stream, error, startCamera, stopCamera } = useCamera();
  const canvasRef = useRef(null);
  const [mode, setMode] = useState("upload");
  const [preview, setPreview] = useState("");

  useEffect(() => () => {
    if (preview.startsWith("blob:")) {
      URL.revokeObjectURL(preview);
    }
  }, [preview]);

  useEffect(() => {
    if (image?.previewUrl) {
      setPreview(image.previewUrl);
    } else {
      setPreview("");
    }
  }, [image]);

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
    <>
      <div className="flex bg-surface-container rounded-none p-1 border-2 border-on-surface">
        <button
          className={`flex-1 py-2 font-label-caps text-label-caps ${mode === "upload" ? "bg-on-surface text-white" : "text-on-surface hover:bg-surface-container-high"}`}
          onClick={() => {
            setMode("upload");
            stopCamera();
          }}
          type="button"
        >
          Upload
        </button>
        <button
          className={`flex-1 py-2 font-label-caps text-label-caps ${mode === "camera" ? "bg-on-surface text-white" : "text-on-surface hover:bg-surface-container-high"}`}
          onClick={() => {
            setMode("camera");
            startCamera();
          }}
          type="button"
        >
          Camera
        </button>
      </div>

      {!preview ? (
          mode === "upload" ? (
            <label className="border-2 border-dashed border-outline bg-surface-container-low h-64 flex flex-col items-center justify-center gap-4 text-outline hover:text-primary hover:border-primary hover:bg-primary-container/5 transition-all cursor-pointer group">
              <span className="material-symbols-outlined text-4xl" style={{fontVariationSettings: "'FILL' 1"}}>photo_camera</span>
              <p className="font-body-md text-center px-8 text-on-surface">Drop your leaf sample here or click to browse</p>
              <input className="hidden" type="file" accept="image/*" onChange={handleFileChange} />
            </label>
          ) : (
            <div className="h-64 relative border-2 border-on-surface overflow-hidden bg-surface-container-low flex flex-col items-center justify-center">
              <video ref={videoRef} autoPlay playsInline className="absolute inset-0 w-full h-full object-cover" />
              <button className="relative z-10 rounded-full bg-primary text-white font-label-caps px-6 py-2 border-2 border-on-surface shadow-[2px_2px_0_0_#191d17]" onClick={handleCapture} type="button">
                Capture Leaf
              </button>
              {error && <p className="relative z-10 text-sm text-error bg-error-container px-2 py-1 mt-2">{error}</p>}
            </div>
          )
      ) : (
          <div className="h-64 border-2 border-on-surface relative">
            <img alt="Selected leaf" className="w-full h-full object-cover border-2 border-transparent" src={preview} />
            <button onClick={onReset} className="absolute top-2 right-2 bg-white border border-on-surface text-on-surface text-xs font-label-caps px-2 py-1">Retake</button>
          </div>
      )}
      <canvas ref={canvasRef} className="hidden" />
    </>
  );
}
