import AudioPlayer from "./AudioPlayer";

function LoadingSpinner({ label }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-8 animate-pulse">
      <span className="material-symbols-outlined text-4xl text-primary" style={{fontVariationSettings: "'FILL' 1"}}>psychiatry</span>
      <span className="font-label-caps text-label-caps text-primary tracking-wider">{label}</span>
      <div className="w-32 h-1 bg-surface-container-high border-x border-on-surface overflow-hidden">
        <div className="bg-primary h-full w-1/2 animate-[bounce_1s_infinite]"></div>
      </div>
    </div>
  );
}

export default function ResultCard({ prediction, advisoryText, advisoryData, isLoading, onReset, onRetry, audioBase64 }) {
  if (!prediction && !isLoading) return null;

  const confidence = prediction?.confidence || 0;

  return (
    <div className="bg-white border-2 border-on-surface overflow-hidden">
        <div className="p-6 border-b-2 border-on-surface bg-surface-bright flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div>
              <span className="font-label-caps text-label-caps text-outline mb-2 block">DIAGNOSIS FOUND</span>
              <h2 className="font-h1 text-h1 text-on-surface">{prediction?.disease || "Analyzing crop condition..."}</h2>
              <p className="font-body-md text-on-surface-variant italic mt-1">{prediction?.crop || ""}</p>
            </div>
            {prediction && (
                <div className="flex flex-col items-end gap-3 mt-1">
                    {advisoryData?.severity && (
                        <span className={`bg-tertiary-container text-on-tertiary-container px-3 py-1 font-data-mono text-xs border-2 border-on-surface uppercase tracking-wider`}>
                            Severity: {advisoryData.severity}
                        </span>
                    )}
                    <div className="flex items-center gap-3">
                        <span className="font-label-caps text-label-caps">Confidence</span>
                        <div className="w-32 h-2 bg-surface-container-high border border-on-surface overflow-hidden">
                            <div className="bg-primary h-full" style={{ width: `${(confidence * 100).toFixed(0)}%` }}></div>
                        </div>
                        <span className="font-data-mono text-data-mono">{(confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>
            )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-0 border-b-2 border-on-surface">
            {/* Immediate Actions */}
            <div className="p-6 border-b-2 md:border-b-0 md:border-r-2 border-on-surface flex flex-col gap-5">
                <h3 className="font-h2 text-h2 flex items-center gap-2 text-primary">
                    <span className="material-symbols-outlined">health_and_safety</span>
                    Treatment & Prevention
                </h3>
                {isLoading ? (
                    <LoadingSpinner label="Consulting knowledge base" />
                ) : (
                    <div className="font-body-md space-y-5">
                        {advisoryData?.treatment && advisoryData.treatment.length > 0 && (
                            <div>
                                <h4 className="font-label-caps text-label-caps text-outline mb-2">TREATMENT</h4>
                                <ul className="space-y-4">
                                    {advisoryData.treatment.slice(0, 3).map((item, i) => (
                                        <li key={i} className="flex gap-3 text-on-surface">
                                            <span className="text-primary font-bold">0{i+1}</span> 
                                            <span className="leading-relaxed">{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {advisoryData?.prevention && advisoryData.prevention.length > 0 && (
                            <div>
                                <h4 className="font-label-caps text-label-caps text-outline mb-2">PREVENTION</h4>
                                <ul className="space-y-4">
                                    {advisoryData.prevention.slice(0, 2).map((item, i) => (
                                        <li key={i+10} className="flex gap-3 text-on-surface">
                                            <span className="text-secondary font-bold">0{i+4}</span> 
                                            <span className="leading-relaxed">{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Agronomist Advisory */}
            <div className="p-6 flex flex-col gap-5 bg-surface-container-lowest relative overflow-hidden">
                <div className="relative z-10">
                    <h3 className="font-h2 text-h2 flex items-center gap-2 text-secondary mb-4">
                        <span className="material-symbols-outlined">lightbulb</span>
                        Agronomist Advisory
                    </h3>
                    <div className="font-body-md text-on-surface-variant leading-relaxed">
                        {advisoryText ? (
                          <div className="whitespace-pre-wrap">{advisoryText}</div>
                        ) : (!isLoading ? "Advisory will appear here." : <LoadingSpinner label="Drafting expert recommendations" />)}
                    </div>
                </div>
                
                {/* Audio Player Integration */}
                {audioBase64 && (
                    <div className="mt-auto pt-6 border-t-2 border-surface-dim relative z-10">
                       <span className="text-xs font-label-caps text-outline mb-3 block">AUDIO ADVISORY (AUTO-PLAYING)</span>
                       <AudioPlayer audioBase64={audioBase64} />
                    </div>
                )}
                <div className="absolute -bottom-8 -right-8 opacity-5 text-secondary z-0 pointer-events-none">
                    <span className="material-symbols-outlined" style={{fontSize: '12rem', fontVariationSettings: "'FILL' 1"}}>eco</span>
                </div>
            </div>
        </div>

        <div className="p-4 bg-surface-container-low flex justify-end gap-3">
             <button className="font-label-caps text-label-caps bg-surface-container-high text-on-surface border-2 border-on-surface px-6 py-2 hover:bg-surface-container-highest transition-colors shadow-[2px_2px_0_0_#191d17]" onClick={onReset} type="button">Reset</button>
             <button className="font-label-caps text-label-caps bg-secondary text-white border-2 border-on-surface px-6 py-2 hover:bg-secondary-container hover:text-on-secondary-container transition-colors shadow-[2px_2px_0_0_#191d17]" onClick={onRetry} type="button">Re-analyze</button>
        </div>
    </div>
  );
}
