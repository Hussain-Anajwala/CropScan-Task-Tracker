import { useState } from "react";

export default function HeatmapOverlay({ imageSrc, heatmapBase64 }) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  if (!imageSrc) return null;

  return (
    <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-stone-200">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-cropscan-leaf">Explainability</h3>
        <button className="rounded-full bg-stone-100 px-3 py-1 text-sm font-medium" onClick={() => setShowHeatmap((value) => !value)} type="button">
          {showHeatmap ? "Hide Heatmap" : "Show Heatmap"}
        </button>
      </div>
      <div className="relative overflow-hidden rounded-2xl">
        <img alt="Leaf scan" className="w-full" src={imageSrc} />
        {showHeatmap && heatmapBase64 ? (
          <img
            alt="Grad-CAM overlay"
            className="absolute inset-0 h-full w-full object-cover opacity-70"
            src={`data:image/png;base64,${heatmapBase64}`}
          />
        ) : null}
      </div>
    </div>
  );
}
