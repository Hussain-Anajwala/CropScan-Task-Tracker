import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

export async function predictDisease(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/predict", formData);
  return data;
}

export async function generateAudio(text, language) {
  const { data } = await api.post("/audio", { text, language });
  return data;
}

export async function generateAdvisory(imageBase64, disease, crop, confidence, language) {
  const { data } = await api.post("/advisory", {
    image: imageBase64,
    disease,
    crop,
    confidence,
    language,
  });
  return data;
}

export async function listDemoSamples() {
  const { data } = await api.get("/demo/samples");
  return data.samples || [];
}
