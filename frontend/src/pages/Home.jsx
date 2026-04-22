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
    <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-10">
      {/* Left Column: Input & Capture */}
      <section className="flex flex-col gap-8">
        <div className="flex items-start justify-between">
            <div>
            <h1 className="font-display text-display text-primary leading-tight mb-2">Identify.<br />Understand.<br />Act.</h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-sm">Precision disease detection powered by Field Intelligence.</p>
            </div>
            <LanguageSelector onChange={setLanguage} value={language} />
        </div>

        {error && <div className="bg-error-container text-on-error-container px-4 py-3 font-body-md border-2 border-on-surface">{error}</div>}
        {statusText && <p className="font-body-md text-primary">{statusText}</p>}

        {/* Demo Samples Strip */}
        <div className="flex flex-col gap-3">
          <span className="font-label-caps text-label-caps text-outline uppercase">Quick Samples</span>
          <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
            {demoSamples.map((sample) => (
              <button
                key={sample.id}
                onClick={() => selectDemoSample(sample)}
                className="shrink-0 w-24 h-24 border-2 border-outline hover:border-primary focus:border-primary transition-all overflow-hidden bg-white"
                title={`${sample.crop} - ${sample.disease}`}
              >
                <img
                  src={`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}${sample.image_url}`}
                  alt={`${sample.crop} sample`}
                  className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all"
                />
              </button>
            ))}
          </div>
        </div>

        {/* Capture Card */}
        <div className="bg-white border-2 border-on-surface p-6 flex flex-col gap-6">
          <CameraCapture onImageChange={setImage} image={image} onReset={resetFlow} />
          
          <button
            className="h-11 bg-primary text-white font-label-caps text-label-caps flex items-center justify-center gap-2 hover:opacity-90 active:translate-y-0.5 transition-all border-2 border-on-surface shadow-[4px_4px_0_0_#191d17] disabled:opacity-50 disabled:shadow-none disabled:active:translate-y-0"
            disabled={!image?.file || isLoading}
            onClick={analyzeLeaf}
            type="button"
          >
            <span className="material-symbols-outlined mb-0.5">analytics</span>
            {isLoading ? "ANALYZING..." : "ANALYZE LEAF"}
          </button>
        </div>
      </section>

      {/* Right Column: Analysis Results */}
      <section className="flex flex-col gap-6">
        <ResultCard
          advisoryData={advisoryData}
          advisoryText={advisory}
          isLoading={isLoading}
          onReset={resetFlow}
          onRetry={analyzeLeaf}
          prediction={prediction}
          audioBase64={audioBase64}
        />
        
        {prediction?.heatmap && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <HeatmapOverlay heatmapBase64={prediction.heatmap} imageSrc={image?.previewUrl || ""} />
             
             {/* Environmental Stats Bento Item */}
             {prediction?.environmental_stats && (
                 <div className="grid grid-cols-1 gap-6">
                    <div className="bg-primary text-white border-2 border-on-surface p-6 flex flex-col justify-between">
                        <div className="flex justify-between items-start">
                        <span className="material-symbols-outlined text-3xl">thermostat</span>
                        <span className="font-label-caps text-label-caps opacity-80 uppercase">{prediction.environmental_stats.sensor}</span>
                        </div>
                        <div>
                        <div className="text-5xl font-display font-black leading-none mb-1">{prediction.environmental_stats.temperature}°C</div>
                        <p className="font-body-md opacity-90">Optimal growth window</p>
                        </div>
                    </div>
                    <div className="bg-secondary-container border-2 border-on-surface p-6 flex flex-col justify-between">
                        <div className="flex justify-between items-start text-on-secondary-container">
                        <span className="material-symbols-outlined text-3xl">humidity_mid</span>
                        <span className="font-label-caps text-label-caps opacity-80 uppercase">Humidity Level</span>
                        </div>
                        <div className="text-on-secondary-container">
                        <div className="text-5xl font-display font-black leading-none mb-1">{prediction.environmental_stats.humidity}%</div>
                        <p className="font-body-md opacity-90 text-on-secondary-container">Pathogen risk elevation</p>
                        </div>
                    </div>
                 </div>
             )}
          </div>
        )}
      </section>
    </div>
  );
}
