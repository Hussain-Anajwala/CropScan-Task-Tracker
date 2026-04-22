import { useEffect, useMemo, useRef, useState } from "react";

export default function AudioPlayer({ audioBase64 }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const source = useMemo(() => {
    if (!audioBase64) return "";
    return `data:audio/wav;base64,${audioBase64}`;
  }, [audioBase64]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  }, [speed]);

  if (!audioBase64) return null;

  function togglePlayback() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play();
      setPlaying(true);
    }
  }

  return (
    <div className="bg-surface-bright flex flex-wrap items-center gap-4">
      <button 
        className="font-label-caps text-label-caps border-2 border-on-surface bg-on-surface text-white px-4 py-2 hover:bg-surface-container-highest hover:text-on-surface transition-colors shadow-[2px_2px_0_0_#191d17]" 
        onClick={togglePlayback} 
        type="button"
      >
        {playing ? "PAUSE" : "PLAY AUDIO"}
      </button>
      <select
        className="bg-transparent font-data-mono text-data-mono border-b-2 border-on-surface px-2 py-1 outline-none text-on-surface hover:bg-surface-container-low transition-colors"
        onChange={(event) => setSpeed(Number(event.target.value))}
        value={speed}
      >
        <option value={0.75}>0.75x Speed</option>
        <option value={1}>1.0x Speed</option>
        <option value={1.25}>1.25x Speed</option>
      </select>
      <audio ref={audioRef} className="hidden" onEnded={() => setPlaying(false)} src={source} />
    </div>
  );
}
