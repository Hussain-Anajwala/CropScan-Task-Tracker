export default function About() {
  return (
    <section className="grid gap-6">
      <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-stone-200">
        <h2 className="text-2xl font-bold text-cropscan-leaf">About CropScan</h2>
        <p className="mt-4 text-base leading-7 text-stone-700">
          CropScan is a final-year project that combines computer vision, a local vision-language
          model, retrieval-augmented agronomy guidance, multilingual translation, and text-to-speech
          to help farmers diagnose crop diseases from leaf photos.
        </p>
      </div>

      <div className="rounded-3xl bg-gradient-to-r from-lime-100 via-amber-50 to-stone-100 p-6 shadow-sm ring-1 ring-stone-200">
        <h3 className="text-xl font-semibold text-cropscan-soil">Technology stack</h3>
        <p className="mt-3 text-sm leading-7 text-stone-700">
          FastAPI, React, PyTorch Lightning, timm, Grad-CAM, Ollama, ChromaDB, MLflow, translation,
          and audio generation are all wired into the current scaffold so the project can grow into
          a full local-first crop advisory tool.
        </p>
      </div>
    </section>
  );
}
