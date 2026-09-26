import React, { useEffect, useRef, useState } from 'react';
import { useParams } from "react-router-dom";
import toWav from 'audiobuffer-to-wav';
import { Mic, Play, Pause, X } from 'lucide-react';
import styles from './VoiceChat.module.css';

type Message = {
  sender: 'user' | 'bot';
  text: string;
  audioBase64?: string;
};

type Props = {
  onClose: () => void;
};

const VoiceChatbot: React.FC<Props> = ({ onClose }) => {
  const { id } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [playingIndex, setPlayingIndex] = useState<number | null>(null);
  const [audioProgress, setAudioProgress] = useState<number>(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const isBotSpeakingRef = useRef(false);
  const streamRef = useRef<MediaStream | null>(null);
  const silenceDetectionActiveRef = useRef(false);
  const isRecordingRef = useRef(false);
  const chatWindowRef = useRef<HTMLDivElement | null>(null);

  const stopAll = () => {
    try {
      console.log("Stopping all audio processing...");
      socketRef.current?.close();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      mediaRecorderRef.current = null;
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.removeAttribute('src');
        audioRef.current.load();
      }
      isRecordingRef.current = false;
    } catch (e) {
      console.warn("Error during cleanup:", e);
    } finally {
      onClose();
    }
  };

  const startMic = async () => {
    try {
      console.log("Requesting microphone access...");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log("Microphone access granted");
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
        audioBitsPerSecond: 128000,
      });

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0 && !isBotSpeakingRef.current) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const chunks = [...audioChunksRef.current];
        audioChunksRef.current = [];

        if (chunks.length === 0) return;

        const blob = new Blob(chunks, { type: 'audio/webm' });
        await sendAudio(blob);

        setTimeout(() => {
          try {
            if (mediaRecorderRef.current?.state === 'inactive') {
              mediaRecorderRef.current.start();
              if (!silenceDetectionActiveRef.current) detectSilence(stream);
              isRecordingRef.current = true;
            }
          } catch (err) {
            console.warn("Failed to restart MediaRecorder:", err);
          }
        }, 200);
      };

      mediaRecorder.start();
      isRecordingRef.current = true;
      detectSilence(stream);
    } catch (err) {
      console.error("Microphone start failed:", err);
    }
  };

  const detectSilence = (stream: MediaStream) => {
    if (silenceDetectionActiveRef.current) return;
    silenceDetectionActiveRef.current = true;

    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);

    const buffer = new Uint8Array(analyser.fftSize);
    let silenceStart = Date.now();
    let speechStarted = false;

    const loop = () => {
      if (isBotSpeakingRef.current) {
        requestAnimationFrame(loop);
        return;
      }

      analyser.getByteTimeDomainData(buffer);
      const rms = Math.sqrt(buffer.reduce((s, v) => s + (v - 128) ** 2, 0) / buffer.length) / 128;

      if (rms < 0.15) {
        if (speechStarted && Date.now() - silenceStart > 1500) {
          if (mediaRecorderRef.current?.state === 'recording') {
            mediaRecorderRef.current.stop();
          }
          ctx.close();
          silenceDetectionActiveRef.current = false;
          isRecordingRef.current = false;
          return;
        }
      } else {
        silenceStart = Date.now();
        speechStarted = true;
      }

      requestAnimationFrame(loop);
    };

    silenceStart = Date.now();
    requestAnimationFrame(loop);
  };

  const sendAudio = async (blob: Blob) => {
    if (isBotSpeakingRef.current) return;
    const buffer = await blob.arrayBuffer();
    const audioCtx = new AudioContext();
    const audioBuffer = await audioCtx.decodeAudioData(buffer);
    const wavBuffer = toWav(audioBuffer);
    const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(wavBlob);
    }
  };

  const handlePlayPause = (audioBase64: string | undefined, index: number) => {
    if (!audioBase64) return;

    if (playingIndex === index && audioRef.current) {
      if (audioRef.current.paused) {
        audioRef.current.play().catch((e) => console.warn("Resume play failed:", e));
      } else {
        audioRef.current.pause();
      }
      return;
    }

    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.src = "";
        audioRef.current.load();
      } catch (e) {
        console.warn("Failed to clean up previous audio:", e);
      }
    }

    const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
    audioRef.current = audio;
    setPlayingIndex(index);
    isBotSpeakingRef.current = true;

    audio.ontimeupdate = () => {
      const progress = (audio.currentTime / audio.duration) * 100;
      setAudioProgress(progress);
    };

    audio.onended = () => {
      isBotSpeakingRef.current = false;
      setAudioProgress(0);
      setPlayingIndex(null);
    };

    audio.onerror = () => {
      isBotSpeakingRef.current = false;
      setPlayingIndex(null);
    };

    setTimeout(() => {
      audio.play().catch((e) => console.warn("Audio play error:", e));
    }, 100);
  };

  const startWebSocket = () => {
    try {
      const socket = new WebSocket('ws://localhost:8000/ws');
      socketRef.current = socket;

      socket.onopen = () => {
        if (id) {
          socket.send(JSON.stringify({ type: "init", property_id: parseInt(id) }));
        }
        setIsListening(true);
        startMic();
      };

      socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'user') {
          setMessages((prev) => [...prev, { sender: 'user', text: data.text }]);
        }

        if (data.type === 'audio') {
          const { text, audio_base64 } = data;
          const newMessage: Message = { sender: 'bot', text, audioBase64: audio_base64 };
          setMessages((prev) => {
            const newMessages = [...prev, newMessage];
            const idx = newMessages.length - 1;
            setTimeout(() => handlePlayPause(audio_base64, idx), 300);
            return newMessages;
          });
        }
      };

      socket.onclose = () => {
        setIsListening(false);
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    } catch (err) {
      console.error("WebSocket start failed:", err);
    }
  };

  useEffect(() => {
    startWebSocket();
    return () => {};
  }, []);
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className={styles.popup} onClick={(e) => e.stopPropagation()}>
      <div className={styles.header}>
        <h2>AI Voice Assistant</h2>
        <button className={styles.closeBtn} onClick={stopAll}><X size={22} /></button>
      </div>

      <div className={styles.micContainer}>
        <div className={`${styles.micIcon} ${isListening ? styles.listening : ''}`}>
          <Mic size={36} />
        </div>
      </div>
      <div className={styles.chatWindow} ref={chatWindowRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`${styles.message} ${msg.sender === 'user' ? styles.user : styles.bot}`}>
            <p>{msg.text}</p>
            {msg.sender === 'bot' && (
              <div className={styles.audioControls}>
                <button onClick={() => handlePlayPause(msg.audioBase64, idx)}>
                  {playingIndex === idx && audioRef.current && !audioRef.current.paused ? (
                    <Pause size={16} />
                  ) : (
                    <Play size={16} />
                  )}
                </button>
                <div className={styles.progressBar}>
                  <div
                    className={styles.progress}
                    style={{ width: playingIndex === idx ? `${audioProgress}%` : '0%' }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className={styles.footer}>
        <button className={styles.endCallBtn} onClick={stopAll}>
          End Call
        </button>
      </div>
    </div>
  );
};

export default VoiceChatbot;
