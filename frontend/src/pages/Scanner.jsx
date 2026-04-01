import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { analyzeMedication } from '../utils/api';
import Icons from '../components/Icons';

function HazardMeter({ score }) {
  const color = score >= 7 ? '#ef4444' : score >= 4 ? '#d97706' : '#22c55e';
  const label = score >= 7 ? 'HIGH' : score >= 4 ? 'MEDIUM' : 'LOW';
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${score * 10}%`, background: color }} />
      </div>
      <span className="text-xs font-bold shrink-0" style={{ color }}>{score}/10 — {label}</span>
    </div>
  );
}

export default function Scanner() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [phase, setPhase] = useState('camera');
  const [facingMode, setFacingMode] = useState('environment');
  const [result, setResult] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);

  const startCamera = useCallback(async () => {
    try {
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch { setPhase('error'); }
  }, [facingMode]);

  useEffect(() => {
    startCamera();
    return () => { if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop()); };
  }, [startCamera]);

  const handleCapture = async () => {
    const video = videoRef.current, canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const blob = await new Promise((r) => canvas.toBlob(r, 'image/jpeg', 0.85));
    setCapturedImage(canvas.toDataURL('image/jpeg', 0.85));
    setPhase('analyzing');
    if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    const { result: res, offline } = await analyzeMedication(blob);
    if (offline) setPhase('offline');
    else { setResult(res); setPhase('result'); }
  };

  const handleRetake = () => { setResult(null); setCapturedImage(null); setPhase('camera'); startCamera(); };

  /* ── Camera phase: full-screen overlay ── */
  if (phase === 'camera') {
    return (
      <div className="fixed inset-0 z-40 bg-black flex flex-col">
        <canvas ref={canvasRef} className="hidden" />
        <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 60% 45%, transparent 50%, rgba(0,0,0,0.6) 100%)' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-48">
            <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-teal-400 rounded-tl-lg" />
            <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-teal-400 rounded-tr-lg" />
            <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-teal-400 rounded-bl-lg" />
            <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-teal-400 rounded-br-lg" />
            <div className="absolute left-2 right-2 h-0.5 bg-gradient-to-r from-transparent via-teal-400 to-transparent animate-scan-line" />
          </div>
          <div className="absolute top-16 left-0 right-0 text-center">
            <p className="text-white/80 text-sm font-medium px-6">Position the medication strip within the frame</p>
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 safe-bottom pb-8">
          <div className="flex items-center justify-center gap-8 px-6">
            <button onClick={() => navigate('/')} className="w-12 h-12 rounded-full glass flex items-center justify-center text-white">
              <Icons.ArrowLeft className="w-5 h-5" />
            </button>
            <button onClick={handleCapture} className="relative w-20 h-20 rounded-full border-4 border-white/90 flex items-center justify-center active:scale-90 transition-transform">
              <div className="w-16 h-16 rounded-full gradient-primary" style={{ boxShadow: 'var(--shadow-accent)' }} />
              <div className="absolute inset-0 rounded-full border-2 border-teal-400/30 animate-pulse-ring" />
            </button>
            <button onClick={() => setFacingMode((p) => p === 'environment' ? 'user' : 'environment')}
                    className="w-12 h-12 rounded-full glass flex items-center justify-center text-white">
              <Icons.RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ── All other phases: render INSIDE Layout (bottom nav stays visible) ── */
  return (
    <div className="px-4 pt-6 pb-6">
      <canvas ref={canvasRef} className="hidden" />

      {phase === 'analyzing' && (
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          {capturedImage && <img src={capturedImage} alt="Captured" className="w-40 h-40 object-cover rounded-2xl mb-6" style={{ boxShadow: 'var(--shadow-lg)' }} />}
          <div className="w-10 h-10 rounded-full border-[3px] border-t-transparent animate-spin mb-4" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
          <p className="font-medium" style={{ color: 'var(--accent)' }}>{t('analyzing')}</p>
          <div className="mt-4 w-48"><div className="skeleton h-2 rounded-full" /></div>
        </div>
      )}

      {phase === 'result' && result && (
        <div className="space-y-4 animate-fade-in-up">
          <div className="flex items-center gap-3 mb-2">
            <button onClick={handleRetake} className="w-10 h-10 rounded-xl card flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>
              <Icons.ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{t('result_title')}</h1>
          </div>

          {capturedImage && <img src={capturedImage} alt="Scanned" className="w-full h-40 object-cover rounded-2xl" />}

          {/* Drug Info */}
          <div className="card p-5" style={{ borderLeft: `3px solid ${result.is_antibiotic ? '#ef4444' : 'var(--accent)'}` }}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-xs uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>{t('drug_detected')}</p>
                <h2 className="text-2xl font-bold mt-1" style={{ color: 'var(--text-primary)' }}>{result.drug_name}</h2>
                <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>{result.drug_type} · {result.drug_class}</p>
              </div>
              <span className="tag" style={{
                background: result.is_antibiotic ? 'rgba(239,68,68,0.1)' : 'var(--accent-bg)',
                color: result.is_antibiotic ? '#ef4444' : 'var(--accent)',
                border: `1px solid ${result.is_antibiotic ? 'rgba(239,68,68,0.2)' : 'rgba(13,148,136,0.2)'}`,
              }}>
                {result.is_antibiotic ? <Icons.AlertTriangle className="w-3 h-3 mr-1" /> : <Icons.CheckCircle className="w-3 h-3 mr-1" />}
                {result.is_antibiotic ? t('antibiotic') : t('general')}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div className="card p-3">
                <p className="text-[10px] uppercase" style={{ color: 'var(--text-tertiary)' }}>{t('confidence')}</p>
                <p className="text-lg font-bold" style={{ color: 'var(--accent)' }}>{Math.round(result.confidence * 100)}%</p>
              </div>
              <div className="card p-3">
                <p className="text-[10px] uppercase" style={{ color: 'var(--text-tertiary)' }}>{t('expiry')}</p>
                <p className="text-sm font-bold" style={{ color: result.expiry_status === 'expired' ? '#ef4444' : result.expiry_status === 'expiring_soon' ? '#d97706' : '#22c55e' }}>
                  {result.expiry_label}
                </p>
              </div>
            </div>
          </div>

          {/* Eco-Hazard */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Icons.AlertTriangle className="w-4 h-4" style={{ color: result.eco_hazard_score >= 7 ? '#ef4444' : result.eco_hazard_score >= 4 ? '#d97706' : '#22c55e' }} />
              <p className="text-xs uppercase tracking-wider font-semibold" style={{ color: 'var(--text-tertiary)' }}>{t('eco_hazard')}</p>
            </div>
            <HazardMeter score={result.eco_hazard_score} />
            <p className="text-sm leading-relaxed mt-3" style={{ color: 'var(--text-secondary)' }}>{result.eco_hazard_info}</p>
          </div>

          {/* Disposal */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-2">
              <Icons.ShieldCheck className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              <p className="text-xs uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>{t('disposal_advice')}</p>
            </div>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{result.disposal_recommendation}</p>
          </div>

          {/* Actions */}
          <div className="space-y-3 pt-2">
            <button onClick={() => navigate('/map', { state: { fromScan: true } })}
                    className="w-full py-4 rounded-2xl gradient-primary text-white font-bold text-sm flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
                    style={{ boxShadow: 'var(--shadow-accent)' }}>
              <Icons.MapPin className="w-4 h-4" />
              {t('find_nearest')}
            </button>
            <button onClick={handleRetake} className="w-full py-4 rounded-2xl card font-semibold text-sm flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
                    style={{ color: 'var(--text-secondary)' }}>
              <Icons.Camera className="w-4 h-4" />
              {t('scan_another')}
            </button>
          </div>
        </div>
      )}

      {phase === 'offline' && (
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <div className="icon-box w-20 h-20 rounded-3xl mb-4 animate-float" style={{ background: 'rgba(245,158,11,0.1)', color: '#d97706' }}>
            <Icons.WifiOff className="w-8 h-8" />
          </div>
          <p className="font-semibold text-lg mb-2 text-center" style={{ color: '#d97706' }}>{t('saved_offline')}</p>
          <p className="text-sm text-center mb-8" style={{ color: 'var(--text-tertiary)' }}>
            Your scan has been queued and will sync automatically when you reconnect.
          </p>
          <div className="space-y-3 w-full max-w-xs">
            <button onClick={handleRetake} className="w-full py-4 rounded-2xl gradient-primary text-white font-bold text-sm flex items-center justify-center gap-2 active:scale-[0.98] transition-transform">
              <Icons.Camera className="w-4 h-4" /> {t('scan_another')}
            </button>
          </div>
        </div>
      )}

      {phase === 'error' && (
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <div className="icon-box w-20 h-20 rounded-3xl mb-4" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
            <Icons.Camera className="w-8 h-8" />
          </div>
          <p className="font-semibold text-lg mb-2" style={{ color: '#ef4444' }}>{t('camera_permission')}</p>
          <p className="text-sm text-center mb-6" style={{ color: 'var(--text-tertiary)' }}>Please grant camera access in your browser settings and try again.</p>
          <button onClick={() => { setPhase('camera'); startCamera(); }}
                  className="px-8 py-3 rounded-2xl gradient-primary text-white font-semibold text-sm active:scale-95 transition-transform">
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
