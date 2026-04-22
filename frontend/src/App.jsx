import { Link, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import About from "./pages/About";
import DemoInstructions from "./pages/DemoInstructions";

export default function App() {
  return (
    <div className="bg-background font-body-md text-on-background min-h-screen pb-20 md:pb-0">
      <header className="bg-emerald-700 h-14 sticky top-0 z-50 border-b-2 border-emerald-900 flex justify-between items-center px-6 w-full max-w-full">
        <div className="text-2xl font-display font-black text-white">CropScan</div>
        <nav className="hidden md:flex gap-8 items-center h-full">
          <Link className="font-display font-bold text-lg tracking-tight text-emerald-100 hover:text-white hover:border-b-2 hover:border-white transition-all pb-1" to="/">Field Map</Link>
          <Link className="font-display font-bold text-lg tracking-tight text-emerald-100 hover:text-white hover:border-b-2 hover:border-white transition-all pb-1" to="/about">Advisory / About</Link>
          <Link className="font-display font-bold text-lg tracking-tight text-emerald-100 hover:text-white hover:border-b-2 hover:border-white transition-all pb-1" to="/demo">Reports / Demo</Link>
        </nav>
        <div className="flex items-center gap-4 text-white">
          <button className="material-symbols-outlined p-2 hover:bg-emerald-600 transition-colors">language</button>
          <div className="w-8 h-8 rounded-full bg-primary-container border-2 border-white overflow-hidden flex items-center justify-center">
            <span className="material-symbols-outlined text-sm">person</span>
          </div>
        </div>
      </header>

      <main className="max-w-[1280px] mx-auto p-6 md:p-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/demo" element={<DemoInstructions />} />
        </Routes>
      </main>

      <footer className="md:hidden fixed bottom-0 left-0 w-full h-16 grid grid-cols-4 items-center bg-white border-t-2 border-on-surface shadow-[0_-4px_0_0_rgba(0,0,0,0.05)] z-50">
        <Link to="/" className="flex flex-col items-center justify-center text-on-surface-variant h-full w-full hover:bg-surface-container-low transition-transform active:translate-y-0.5">
          <span className="material-symbols-outlined">agriculture</span>
          <span className="font-label-caps text-[11px] uppercase tracking-wider mt-1">Fields</span>
        </Link>
        <Link to="/" className="flex flex-col items-center justify-center bg-primary text-white border-2 border-on-surface h-full w-full active:translate-y-0.5">
          <span className="material-symbols-outlined" style={{fontVariationSettings: "'FILL' 1"}}>photo_camera</span>
          <span className="font-label-caps text-[11px] uppercase tracking-wider mt-1">Scan</span>
        </Link>
        <Link to="/about" className="flex flex-col items-center justify-center text-on-surface-variant h-full w-full hover:bg-surface-container-low transition-transform active:translate-y-0.5">
          <span className="material-symbols-outlined">analytics</span>
          <span className="font-label-caps text-[11px] uppercase tracking-wider mt-1">Insights</span>
        </Link>
        <Link to="/demo" className="flex flex-col items-center justify-center text-on-surface-variant h-full w-full hover:bg-surface-container-low transition-transform active:translate-y-0.5">
          <span className="material-symbols-outlined">person</span>
          <span className="font-label-caps text-[11px] uppercase tracking-wider mt-1">Profile</span>
        </Link>
      </footer>
    </div>
  );
}
