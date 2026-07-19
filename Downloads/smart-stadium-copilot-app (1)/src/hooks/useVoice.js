import { useState, useRef, useCallback } from "react";

const SpeechRecognitionAPI =
  typeof window !== "undefined" ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;

/** Native browser speech-to-text — no API key, no cost, works offline-capable in supporting browsers. */
export function useVoiceInput(langCode, onResult) {
  const [listening, setListening] = useState(false);
  const recRef = useRef(null);

  const toggle = useCallback(() => {
    if (!SpeechRecognitionAPI) return;
    if (listening) { recRef.current?.stop(); setListening(false); return; }
    const rec = new SpeechRecognitionAPI();
    rec.lang = langCode || "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      const t = e.results?.[0]?.[0]?.transcript;
      if (t) onResult(t);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    rec.start();
    setListening(true);
  }, [listening, langCode, onResult]);

  return { listening, toggle, supported: !!SpeechRecognitionAPI };
}

/** Native browser text-to-speech, for reading AI responses aloud. */
export function speak(text, langCode) {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = langCode || "en-US";
  window.speechSynthesis.speak(utter);
}
