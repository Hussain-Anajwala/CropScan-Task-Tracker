export default function DemoInstructions() {
  return (
    <section className="grid gap-6">
      <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-stone-200">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cropscan-soil">Demo Instructions</p>
        <h2 className="mt-2 text-3xl font-bold text-cropscan-leaf">Run a clean CropScan demo in under a minute.</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl bg-lime-50 p-5">
            <h3 className="font-semibold text-cropscan-leaf">Before presenting</h3>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-stone-700">
              <li>- Start the FastAPI backend and React frontend.</li>
              <li>- Keep Ollama running if you want live VLM advisories.</li>
              <li>- If Ollama is unavailable, the fallback advisory still works.</li>
              <li>- Open the Home page and preload one sample image.</li>
            </ul>
          </div>
          <div className="rounded-2xl bg-amber-50 p-5">
            <h3 className="font-semibold text-cropscan-soil">Suggested demo script</h3>
            <ol className="mt-3 space-y-2 text-sm leading-6 text-stone-700">
              <li>1. Pick a demo sample or upload a leaf image.</li>
              <li>2. Click Analyze Leaf and point out the confidence bar.</li>
              <li>3. Show the Grad-CAM heatmap and disease label.</li>
              <li>4. Read the treatment and prevention bullets aloud.</li>
            </ol>
          </div>
        </div>
      </div>

      <div className="rounded-3xl bg-gradient-to-r from-lime-100 via-stone-50 to-amber-100 p-6 shadow-sm ring-1 ring-stone-200">
        <h3 className="text-xl font-semibold text-stone-900">Talking points</h3>
        <p className="mt-3 text-sm leading-7 text-stone-700">
          CropScan combines a trained plant-disease classifier, explainability with Grad-CAM, retrieval-augmented agronomy
          guidance, fallback advisory logic, translation, and text-to-speech. The demo is designed to stay reliable even
          when external model services are unavailable.
        </p>
      </div>
    </section>
  );
}
