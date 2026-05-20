import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPharmacyRequests, acceptRequest, generateOtp, getRequestStatus } from '../../utils/api';

function getSession() {
  try {
    const s = JSON.parse(localStorage.getItem('amr-pharmacy-session') || 'null');
    if (!s || Date.now() > s.expires_at) return null;
    return s;
  } catch { return null; }
}

function timeAgo(iso) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function StatusBadge({ status }) {
  const map = {
    PENDING:       { bg: 'rgba(251,191,36,0.15)',  color: '#fbbf24', label: 'Pending' },
    ACCEPTED:      { bg: 'rgba(59,130,246,0.15)',   color: '#60a5fa', label: 'Accepted' },
    OTP_GENERATED: { bg: 'rgba(167,139,250,0.2)',   color: '#a78bfa', label: 'OTP Active' },
    COMPLETED:     { bg: 'rgba(34,197,94,0.15)',    color: '#4ade80', label: 'Completed' },
  };
  const s = map[status] || { bg: 'rgba(255,255,255,0.1)', color: '#9ca3af', label: status };
  return (
    <span style={{ fontSize: '11px', fontWeight: '700', padding: '3px 10px', borderRadius: '20px', background: s.bg, color: s.color, letterSpacing: '0.03em', whiteSpace: 'nowrap' }}>
      {s.label}
    </span>
  );
}

function OtpModal({ request, onClose, onComplete }) {
  const [otp, setOtp] = useState(null);
  const [expiresAt, setExpiresAt] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(600);
  const [generating, setGenerating] = useState(false);
  const [completed, setCompleted] = useState(false);
  const session = getSession();
  const pollRef = useRef(null);
  const timerRef = useRef(null);

  const doGenerateOtp = useCallback(async () => {
    setGenerating(true);
    try {
      const res = await generateOtp(request.id, session.token);
      setOtp(res.otp);
      setExpiresAt(new Date(res.expires_at).getTime());
      setSecondsLeft(res.expires_in_seconds);
    } catch (e) {
      alert('Failed to generate OTP: ' + e.message);
    } finally {
      setGenerating(false);
    }
  }, [request.id, session.token]);

  useEffect(() => {
    if (request.status === 'ACCEPTED') doGenerateOtp();
    if (request.status === 'OTP_GENERATED' && request.otp) {
      setOtp(request.otp);
      const exp = new Date(request.otp_expires_at).getTime();
      setExpiresAt(exp);
      setSecondsLeft(Math.max(0, Math.floor((exp - Date.now()) / 1000)));
    }
  }, []);

  useEffect(() => {
    if (!expiresAt) return;
    timerRef.current = setInterval(() => {
      const left = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      setSecondsLeft(left);
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [expiresAt]);

  useEffect(() => {
    if (!otp) return;
    pollRef.current = setInterval(async () => {
      try {
        const data = await getRequestStatus(request.id, session.token);
        if (data.status === 'COMPLETED') {
          clearInterval(pollRef.current);
          setCompleted(true);
          setTimeout(() => { onComplete(); onClose(); }, 2500);
        }
        if (data.status === 'ACCEPTED') { setOtp(null); setSecondsLeft(0); }
      } catch {}
    }, 5000);
    return () => clearInterval(pollRef.current);
  }, [otp]);

  const mins = String(Math.floor(secondsLeft / 60)).padStart(2, '0');
  const secs = String(secondsLeft % 60).padStart(2, '0');
  const reqLabel = request.req_number || `#${request.id?.slice(0, 8)}`;

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: 'linear-gradient(160deg, #1e1b4b, #0f172a)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '20px', padding: '28px', width: '100%', maxWidth: '340px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
          <div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>OTP Verification</div>
            <div style={{ color: 'white', fontWeight: '700', fontSize: '15px' }}>{reqLabel} · {request.drug_name}</div>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.08)', border: 'none', color: 'rgba(255,255,255,0.6)', width: '30px', height: '30px', borderRadius: '8px', cursor: 'pointer', fontSize: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>×</button>
        </div>

        {completed ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎉</div>
            <p style={{ color: '#4ade80', fontWeight: '700', fontSize: '16px' }}>Verified! Points credited.</p>
          </div>
        ) : generating ? (
          <div style={{ textAlign: 'center', padding: '30px 0', color: 'rgba(255,255,255,0.5)' }}>Generating OTP…</div>
        ) : otp ? (
          <>
            <div style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '16px', padding: '20px', textAlign: 'center', marginBottom: '16px' }}>
              <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Share with user</p>
              <div style={{ fontSize: '40px', fontWeight: '900', letterSpacing: '0.2em', color: 'white', fontFamily: 'monospace' }}>{otp}</div>
              <p style={{ color: secondsLeft < 60 ? '#f87171' : 'rgba(255,255,255,0.4)', fontSize: '12px', marginTop: '8px', fontWeight: '600' }}>
                Expires in {mins}:{secs}
              </p>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '11px', textAlign: 'center', lineHeight: '1.5' }}>
              Read this code to the user. They enter it in the app under "My Requests" to complete the transaction.
            </p>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', marginBottom: '16px' }}>OTP expired. Generate a new one.</p>
            <button onClick={doGenerateOtp} style={{ padding: '11px 24px', borderRadius: '10px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: 'white', fontWeight: '700', border: 'none', cursor: 'pointer' }}>
              Generate New OTP
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function RequestCard({ req, onAccept, onOpenOtp }) {
  const isAntibiotic = req.is_antibiotic;
  const isBundle = req.items && req.items.length > 1;
  const [showItems, setShowItems] = useState(false);
  const reqLabel = req.req_number || `#${req.id?.slice(0, 8)}`;

  return (
    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '14px', padding: '16px', marginBottom: '10px' }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Request number badge */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <span style={{ fontSize: '12px', fontWeight: '800', color: '#a78bfa', fontFamily: 'monospace', background: 'rgba(139,92,246,0.15)', padding: '2px 8px', borderRadius: '6px' }}>
              {reqLabel}
            </span>
            {isAntibiotic && <span style={{ fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '20px', background: 'rgba(239,68,68,0.15)', color: '#f87171' }}>Antibiotic</span>}
            {isBundle && <span style={{ fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '20px', background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}>Bundle ×{req.items.length}</span>}
          </div>
          <div style={{ color: 'white', fontWeight: '600', fontSize: '14px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {req.drug_name}
          </div>
          <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: '12px', marginTop: '2px' }}>
            Qty {req.quantity} · {timeAgo(req.created_at)}
          </div>
        </div>
        <StatusBadge status={req.status} />
      </div>

      {/* Bundle items expandable */}
      {isBundle && (
        <div style={{ marginBottom: '10px' }}>
          <button
            onClick={() => setShowItems(v => !v)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(165,180,252,0.8)', fontSize: '12px', fontWeight: '600', padding: 0 }}
          >
            {showItems ? 'Hide' : 'View'} {req.items.length} medicines ▾
          </button>
          {showItems && (
            <div style={{ marginTop: '8px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '8px' }}>
              {req.items.map((item, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '3px 0', color: 'rgba(255,255,255,0.5)' }}>
                  <span>{item.drug_name} ({item.medicine_type}) ×{item.quantity}</span>
                  <span style={{ color: '#a78bfa', fontWeight: '600' }}>+{item.is_antibiotic ? 70 : 50}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Points */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '9px 12px', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', marginBottom: '12px' }}>
        <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px' }}>Points on completion</span>
        <span style={{ color: '#a78bfa', fontWeight: '800', fontSize: '15px' }}>+{req.total_points} pts</span>
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {req.status === 'PENDING' && (
          <button onClick={() => onAccept(req.id)}
            style={{ flex: 1, padding: '11px', borderRadius: '10px', background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.3)', color: '#fbbf24', fontWeight: '700', fontSize: '13px', cursor: 'pointer' }}>
            Accept
          </button>
        )}
        {(req.status === 'ACCEPTED' || req.status === 'OTP_GENERATED') && (
          <button onClick={() => onOpenOtp(req)}
            style={{ flex: 1, padding: '11px', borderRadius: '10px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: 'white', fontWeight: '700', fontSize: '13px', border: 'none', cursor: 'pointer', boxShadow: '0 4px 12px rgba(99,102,241,0.3)' }}>
            {req.status === 'OTP_GENERATED' ? 'View OTP' : 'Medicines Received → OTP'}
          </button>
        )}
      </div>
    </div>
  );
}

const TABS = [
  { key: 'pending',    label: 'Pending',     icon: '⏳' },
  { key: 'inprogress', label: 'In Progress',  icon: '🔄' },
  { key: 'completed',  label: 'Completed',   icon: '✅' },
];

export default function PharmacyDashboard() {
  const navigate = useNavigate();
  const session = getSession();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeOtpReq, setActiveOtpReq] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');
  const [lastRefresh, setLastRefresh] = useState(null);

  useEffect(() => {
    if (!session) { navigate('/pharmacy/login'); }
  }, []);

  const fetchRequests = useCallback(async () => {
    if (!session) return;
    try {
      const res = await getPharmacyRequests(session.token);
      setRequests(res.requests || []);
      setLastRefresh(new Date());
    } catch (e) {
      if (e.message?.includes('401')) { localStorage.removeItem('amr-pharmacy-session'); navigate('/pharmacy/login'); }
    } finally {
      setLoading(false);
    }
  }, [session?.token]);

  useEffect(() => { fetchRequests(); }, [fetchRequests]);

  useEffect(() => {
    const t = setInterval(fetchRequests, 30000);
    return () => clearInterval(t);
  }, [fetchRequests]);

  const handleAccept = async (requestId) => {
    try {
      await acceptRequest(requestId, session.token);
      await fetchRequests();
      setActiveTab('inprogress'); // jump to in-progress after accepting
    } catch (e) { alert(e.message); }
  };

  const logout = () => {
    localStorage.removeItem('amr-pharmacy-session');
    navigate('/pharmacy/login');
  };

  if (!session) return null;

  const pending    = requests.filter(r => r.status === 'PENDING');
  const inProgress = requests.filter(r => r.status === 'ACCEPTED' || r.status === 'OTP_GENERATED');
  const completed  = requests.filter(r => r.status === 'COMPLETED');

  const tabData = {
    pending:    pending,
    inprogress: inProgress,
    completed:  completed,
  };
  const visibleRequests = tabData[activeTab] || [];

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'linear-gradient(160deg, #0f172a 0%, #1e1b4b 60%, #0f172a 100%)', fontFamily: "'Inter', sans-serif", color: 'white', overflow: 'hidden' }}>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* ── Sticky Header ── */}
      <div style={{ flexShrink: 0, padding: '16px 20px 12px', borderBottom: '1px solid rgba(255,255,255,0.07)', background: 'rgba(15,23,42,0.95)', backdropFilter: 'blur(16px)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              </svg>
            </div>
            <div>
              <p style={{ fontSize: '15px', fontWeight: '800', margin: 0, lineHeight: 1.2 }}>{session.pharmacy_name}</p>
              <p style={{ fontSize: '10px', color: 'rgba(255,255,255,0.35)', margin: 0 }}>
                {lastRefresh ? `Updated ${timeAgo(lastRefresh.toISOString())}` : 'Loading…'}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button onClick={fetchRequests} style={{ padding: '7px 12px', borderRadius: '8px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.7)', fontSize: '12px', cursor: 'pointer', fontWeight: '600' }}>
              ↻
            </button>
            <button onClick={logout} style={{ padding: '7px 12px', borderRadius: '8px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171', fontSize: '12px', cursor: 'pointer', fontWeight: '600' }}>
              Logout
            </button>
          </div>
        </div>

        {/* ── Stat Cards (clickable) ── */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
          {[
            { key: 'pending',    label: 'Pending',     value: pending.length,    color: '#fbbf24' },
            { key: 'inprogress', label: 'In Progress',  value: inProgress.length, color: '#60a5fa' },
            { key: 'completed',  label: 'Completed',   value: completed.length,  color: '#4ade80' },
          ].map(s => (
            <button
              key={s.key}
              onClick={() => setActiveTab(s.key)}
              style={{
                flex: 1, padding: '10px 6px', borderRadius: '10px', textAlign: 'center', cursor: 'pointer', border: 'none',
                background: activeTab === s.key ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.04)',
                outline: activeTab === s.key ? `1.5px solid ${s.color}40` : 'none',
                transition: 'all 0.15s',
              }}
            >
              <div style={{ fontSize: '22px', fontWeight: '800', color: s.color, lineHeight: 1 }}>{s.value}</div>
              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', marginTop: '3px', fontWeight: '600' }}>{s.label}</div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Tab Nav ── */}
      <div style={{ flexShrink: 0, display: 'flex', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              flex: 1, padding: '11px 4px', fontSize: '12px', fontWeight: '700', cursor: 'pointer',
              background: 'none', border: 'none',
              color: activeTab === tab.key ? 'white' : 'rgba(255,255,255,0.35)',
              borderBottom: activeTab === tab.key ? '2px solid #8b5cf6' : '2px solid transparent',
              transition: 'all 0.15s',
            }}
          >
            {tab.icon} {tab.label}
            {tab.key === 'pending' && pending.length > 0 && (
              <span style={{ marginLeft: '4px', fontSize: '10px', background: '#fbbf24', color: '#000', borderRadius: '10px', padding: '1px 5px', fontWeight: '800' }}>
                {pending.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Scrollable Content ── */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', padding: '14px 16px 24px', WebkitOverflowScrolling: 'touch' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'rgba(255,255,255,0.3)' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '3px solid rgba(99,102,241,0.3)', borderTopColor: '#6366f1', animation: 'spin 1s linear infinite', margin: '0 auto 12px' }} />
            Loading…
          </div>
        ) : visibleRequests.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div style={{ fontSize: '40px', marginBottom: '12px' }}>
              {activeTab === 'pending' ? '📭' : activeTab === 'inprogress' ? '⏳' : '✅'}
            </div>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px' }}>
              No {TABS.find(t => t.key === activeTab)?.label.toLowerCase()} requests.
            </p>
            <p style={{ color: 'rgba(255,255,255,0.2)', fontSize: '12px' }}>Auto-refreshes every 30s.</p>
          </div>
        ) : (
          visibleRequests.map(r => (
            <RequestCard key={r.id} req={r} onAccept={handleAccept} onOpenOtp={setActiveOtpReq} />
          ))
        )}
      </div>

      {/* OTP Modal */}
      {activeOtpReq && (
        <OtpModal
          request={activeOtpReq}
          onClose={() => setActiveOtpReq(null)}
          onComplete={fetchRequests}
        />
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
