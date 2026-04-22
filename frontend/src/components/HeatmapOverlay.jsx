import { useState } from "react";

export default function HeatmapOverlay({ imageSrc, heatmapBase64 }) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  if (!imageSrc) return null;

  return (
    <div className="bg-white border-2 border-on-surface overflow-hidden">
      <div className="p-4 border-b-2 border-on-surface bg-surface-container flex items-center justify-between">
        <h3 className="font-label-caps text-label-caps text-on-surface">EXPLAINABILITY</h3>
        <button 
          className="font-label-caps text-label-caps bg-on-surface text-white px-4 py-1 hover:bg-surface-container-highest hover:text-on-surface transition-colors shadow-[2px_2px_0_0_#191d17]" 
          onClick={() => setShowHeatmap((value) => !value)} 
          type="button"
        >
          {showHeatmap ? "HIDE HEATMAP" : "SHOW HEATMAP"}
        </button>
      </div>
      <div className="relative overflow-hidden bg-surface-container-low min-h-64 flex items-center justify-center">
        <img alt="Leaf scan" className="w-full h-full object-cover" src={imageSrc} />
        {showHeatmap && heatmapBase64 ? (
          <img
            alt="Grad-CAM overlay"
            className="absolute inset-0 h-full w-full object-cover mix-blend-multiply opacity-80"
            src={`data:image/png;base64,${heatmapBase64}`}
          />
        ) : null}
      </div>
    </div>
  );
}
