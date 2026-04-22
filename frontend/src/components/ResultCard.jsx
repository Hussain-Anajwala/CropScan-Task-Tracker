function confidenceClass(confidence) {
  if (confidence >= 0.9) return "bg-emerald-100 text-emerald-700";
  if (confidence >= 0.7) return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-700";
}

function severityClass(severity) {
  const normalized = String(severity || "").toLowerCase();
  if (normalized.includes("low")) return "bg-emerald-100 text-emerald-700";
  if (normalized.includes("moderate")) return "bg-yellow-100 text-yellow-800";
  if (normalized.includes("high")) return "bg-orange-100 text-orange-800";
  return "bg-red-100 text-red-700";
}

function LoadingSpinner({ label }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-600">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-stone-300 border-t-cropscan-leaf" />
      <span>{label}</span>
    </div>
  );
}

export default function ResultCard({ prediction, advisoryText, advisoryData, isLoading, onReset, onRetry }) {
  if (!prediction && !isLoading) return null;

  const confidence = prediction?.confidence || 0;

  return (
    <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-stone-200">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cropscan-soil">Scan Result</p>
          <h3 className="mt-2 text-2xl font-bold text-cropscan-leaf">
            {prediction?.disease || "Analyzing crop condition..."}
          </h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {prediction ? (
            <span className={`rounded-full px-3 py-1 text-sm font-semibold ${confidenceClass(confidence)}`}>
              {(confidence * 100).toFixed(1)}% confidence
            </span>
          ) : null}
          {advisoryData?.severity ? (
            <span className={`rounded-full px-3 py-1 text-sm font-semibold ${severityClass(advisoryData.severity)}`}>
              {advisoryData.severity}
            </span>
          ) : null}
        </div>
      </div>

      {prediction ? (
        <div className="mt-5 rounded-2xl bg-stone-50 p-4">
          <div className="flex items-center justify-between text-sm font-medium text-stone-600">
            <span>Model confidence</span>
            <span>{(confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full bg-stone-200">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber-400 via-lime-500 to-emerald-600"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
        </div>
      ) : null}

      <div className="mt-5 rounded-2xl bg-stone-50 p-4">
        {prediction?.top_k?.length ? (
          <div className="mb-4 flex flex-wrap gap-2">
            {prediction.top_k.map((item) => (
              <span key={item.class} className="rounded-full bg-stone-200 px-3 py-1 text-xs font-medium text-stone-700">
                {item.disease} {(item.confidence * 100).toFixed(1)}%
              </span>
            ))}
          </div>
        ) : null}
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-stone-500">Advisory</p>
        {isLoading ? <LoadingSpinner label="Generating prediction and advisory..." /> : null}
        <p className="mt-3 whitespace-pre-wrap text-base leading-7 text-stone-700">
          {advisoryText || (!isLoading ? "Advisory will appear here." : "")}
        </p>
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <button className="rounded-full bg-cropscan-leaf px-4 py-2 text-sm font-semibold text-white" onClick={onRetry} type="button">
          Retry Analysis
        </button>
        <button className="rounded-full bg-stone-100 px-4 py-2 text-sm font-semibold text-stone-700" onClick={onReset} type="button">
          Reset
        </button>
      </div>

      {advisoryData ? (
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl bg-lime-50 p-4">
            <h4 className="font-semibold text-cropscan-leaf">Treatment</h4>
            <ul className="mt-3 space-y-2 text-sm text-stone-700">
              {advisoryData.treatment?.map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl bg-amber-50 p-4">
            <h4 className="font-semibold text-cropscan-soil">Prevention</h4>
            <ul className="mt-3 space-y-2 text-sm text-stone-700">
              {advisoryData.prevention?.map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
}
