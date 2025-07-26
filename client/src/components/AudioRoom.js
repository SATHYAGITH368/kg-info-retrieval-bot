import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';

const AudioRoom = ({ onTranscript }) => {
  const [isMuted, setIsMuted] = useState(true);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);
  const isRecognizingRef = useRef(false);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Web Speech API is not supported in this browser.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;  // Keep listening continuously
    recognition.interimResults = false; // Only final results
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const lastResultIndex = event.results.length - 1;
      const result = event.results[lastResultIndex][0].transcript;
      console.log("Voice input result:", result);
      setTranscript(result);
      if (onTranscript) {
        onTranscript(result);
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      // Optional: you can restart recognition here if needed
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        // User denied permission or service disabled, handle accordingly
        setIsMuted(true);
      } else if (event.error === 'network' || event.error === 'no-speech') {
        // Could try restarting recognition
        if (!isMuted) {
          try {
            recognition.stop();
            recognition.start();
          } catch {}
        }
      }
    };

    recognition.onend = () => {
      isRecognizingRef.current = false;
      console.log("Speech recognition ended.");
      // Automatically restart if not muted (to keep it going forever)
      if (!isMuted) {
        try {
          recognition.start();
          isRecognizingRef.current = true;
        } catch (e) {
          // Can throw if recognition is already started
          console.warn("Recognition start failed on end:", e);
        }
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      recognition.stop();
      isRecognizingRef.current = false;
    };
  }, [onTranscript, isMuted]);

  useEffect(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    if (!isMuted && !isRecognizingRef.current) {
      try {
        recognition.start();
        isRecognizingRef.current = true;
        console.log("Speech recognition started.");
      } catch (e) {
        console.warn("Recognition start failed:", e);
      }
    }

    if (isMuted && isRecognizingRef.current) {
      try {
        recognition.stop();
        isRecognizingRef.current = false;
        console.log("Speech recognition stopped.");
      } catch (e) {
        console.warn("Recognition stop failed:", e);
      }
    }
  }, [isMuted]);

  const toggleMute = () => {
    setIsMuted(prev => !prev);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <button
        onClick={toggleMute}
        style={{
          padding: '6px 10px',
          borderRadius: '6px',
          border: '1px solid #ccc',
          backgroundColor: isMuted ? '#f8d7da' : '#d4edda',
          cursor: 'pointer'
        }}
      >
        {isMuted ? <MicOff size={16} /> : <Mic size={16} />} {isMuted ? 'Unmute' : 'Mute'}
      </button>
      <span style={{ fontSize: 14, color: '#555' }}>{transcript}</span>
    </div>
  );
};

export default AudioRoom;
