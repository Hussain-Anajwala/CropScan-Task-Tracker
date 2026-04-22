import { useEffect, useState } from "react";
import { generateAdvisory, generateAudio, listDemoSamples, predictDisease } from "../api/cropscan";
import AudioPlayer from "../components/AudioPlayer";
import CameraCapture from "../components/CameraCapture";
import HeatmapOverlay from "../components/HeatmapOverlay";
import LanguageSelector from "../components/LanguageSelector";
import ResultCard from "../components/ResultCard";

export default function Home() {
  const [image, setImage] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [advisory, setAdvisory] = useState("");
  const [advisoryData, setAdvisoryData] = useState(null);
  const [audioBase64, setAudioBase64] = useState("");
  const [language, setLanguage] = useState("en");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusText, setStatusText] = useState("");
  const [demoSamples, setDemoSamples] = useState([]);

  useEffect(() => {
    if (!advisoryData?.advisory) return;
    generateAudio(advisoryData.advisory, language)
      .then((response) => setAudioBase64(response.audio))
      .catch((err) => setError(err.message || "Audio generation failed."));
  }, [advisoryData, language]);

  useEffect(() => {
    listDemoSamples()
      .then(setDemoSamples)
      .catch(() => setDemoSamples([]));
  }, []);

  async function selectDemoSample(sample) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const response = await fetch(`${baseUrl}${sample.image_url}`);
    const blob = await response.blob();
    const file = new File([blob], `${sample.id}.jpg`, { type: blob.type || "image/jpeg" });
    const advisoryImageBase64 = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || "").split(",")[1] || "");
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
    const previewUrl = URL.createObjectURL(file);
    setImage({ file, previewUrl, advisoryImageBase64 });
    setPrediction(null);
    setAdvisory("");
    setAdvisoryData(null);
    setAudioBase64("");
    setError("");
  }

  function resetFlow() {
    setImage(null);
    setPrediction(null);
    setAdvisory("");
    setAdvisoryData(null);
    setAudioBase64("");
    setError("");
    setStatusText("");
  }

  async function analyzeLeaf() {
    if (!image?.file) return;
    setIsLoading(true);
    setError("");
    setAdvisory("");
    setAdvisoryData(null);
    setAudioBase64("");
    setStatusText("Running disease prediction...");

    try {
      const predictionResult = await predictDisease(image.file);
      setPrediction(predictionResult);

      setStatusText("Generating agronomy advisory...");
      const advisoryResult = await generateAdvisory(
        image.advisoryImageBase64,
        predictionResult.disease,
        predictionResult.crop,
        predictionResult.confidence,
        language,
      );
      setAdvisoryData(advisoryResult);
      setAdvisory(advisoryResult.advisory || "");
      setStatusText("Analysis complete.");
    } catch (err) {
      setError(err.message || "Analysis failed.");
      setStatusText("Analysis failed. You can retry or reset.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cropscan-soil">Field-ready scan flow</p>
          <h2 className="mt-2 text-3xl font-bold text-stone-900">Capture a leaf and get an advisory.</h2>
          {statusText ? <p className="mt-2 text-sm text-stone-600">{statusText}</p> : null}
        </div>
        <LanguageSelector onChange={setLanguage} value={language} />
      </div>

      {error ? <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      {demoSamples.length ? (
        <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-stone-200">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cropscan-soil">Demo Mode</p>
              <h3 className="mt-1 text-lg font-semibold text-stone-900">Use a prepared sample image</h3>
            </div>
            <span className="text-sm text-stone-500">Fastest way to show the full pipeline live</span>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {demoSamples.map((sample) => (
              <button
                key={sample.id}
                className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-left transition hover:border-cropscan-leaf hover:bg-lime-50"
                onClick={() => selectDemoSample(sample)}
                type="button"
              >
                <p className="font-semibold text-stone-900">{sample.crop}</p>
                <p className="mt-1 text-sm text-stone-600">{sample.disease}</p>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-6">
          <CameraCapture onImageChange={setImage} />
          <button
            className="w-full rounded-full bg-cropscan-leaf px-5 py-3 text-base font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:bg-stone-400"
            disabled={!image?.file || isLoading}
            onClick={analyzeLeaf}
            type="button"
          >
            {isLoading ? "Analyzing..." : "Analyze Leaf"}
          </button>
        </div>

        <div className="space-y-6">
          <ResultCard
            advisoryData={advisoryData}
            advisoryText={advisory}
            isLoading={isLoading}
            onReset={resetFlow}
            onRetry={analyzeLeaf}
            prediction={prediction}
          />
          {prediction ? <HeatmapOverlay heatmapBase64={prediction.heatmap} imageSrc={image?.previewUrl || ""} /> : null}
          <AudioPlayer audioBase64={audioBase64} />
        </div>
      </div>
    </section>
  );
}
