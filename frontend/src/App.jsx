import { Link, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import About from "./pages/About";
import DemoInstructions from "./pages/DemoInstructions";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-lime-50 via-stone-50 to-amber-50 text-stone-900">
      <header className="border-b border-stone-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cropscan-soil">
              CropScan
            </p>
            <h1 className="text-xl font-bold text-cropscan-leaf">
              Multimodal crop disease advisory
            </h1>
          </div>
          <nav className="flex gap-4 text-sm font-medium">
            <Link to="/">Home</Link>
            <Link to="/about">About</Link>
            <Link to="/demo">Demo</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-10">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/demo" element={<DemoInstructions />} />
        </Routes>
      </main>
    </div>
  );
}
