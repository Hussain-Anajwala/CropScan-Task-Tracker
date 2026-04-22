const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "ta", label: "Tamil" },
  { code: "te", label: "Telugu" },
  { code: "mr", label: "Marathi" },
];

export default function LanguageSelector({ value, onChange }) {
  return (
    <label className="flex items-center gap-3 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-stone-200">
      <span className="text-sm font-semibold text-stone-600">Language</span>
      <select className="bg-transparent text-sm font-medium outline-none" onChange={(event) => onChange(event.target.value)} value={value}>
        {LANGUAGES.map((language) => (
          <option key={language.code} value={language.code}>
            {language.label}
          </option>
        ))}
      </select>
    </label>
  );
}
