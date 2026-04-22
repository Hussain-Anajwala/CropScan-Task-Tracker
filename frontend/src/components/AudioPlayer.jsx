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
    <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-stone-200">
      <div className="flex flex-wrap items-center gap-3">
        <button className="rounded-full bg-cropscan-leaf px-4 py-2 font-semibold text-white" onClick={togglePlayback} type="button">
          {playing ? "Pause" : "Play"}
        </button>
        <select
          className="rounded-full border border-stone-300 bg-white px-4 py-2"
          onChange={(event) => setSpeed(Number(event.target.value))}
          value={speed}
        >
          <option value={0.75}>0.75x</option>
          <option value={1}>1x</option>
          <option value={1.25}>1.25x</option>
        </select>
      </div>
      <audio ref={audioRef} className="mt-4 w-full" controls onEnded={() => setPlaying(false)} src={source} />
    </div>
  );
}
