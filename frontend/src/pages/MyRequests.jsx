import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRewards } from '../contexts/RewardsContext';
import { getUserRequests, claimTakeBackPoints } from '../utils/api';
import Icons from '../components/Icons';

function timeAgo(iso) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

const STATUS_MAP = {
  PENDING:       { label: 'Pending',     color: '#d97706', bg: 'rgba(251,191,36,0.12)' },
  ACCEPTED:      { label: 'Accepted',    color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' },
  OTP_GENERATED: { label: 'OTP Ready',   color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)' },
  COMPLETED:     { label: 'Completed',   color: '#16a34a', bg: 'rgba(22,163,74,0.12)'  },
  EXPIRED:       { label: 'Expired',     color: '#9ca3af', bg: 'rgba(156,163,175,0.12)'},
};

function OtpEntry({ request, onSuccess }) {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { deviceId, refresh } = useRewards();

  const handleClaim = async () => {
    if (otp.length !== 6) { setError('OTP must be 6 digits.'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await claimTakeBackPoints(request.id, otp, deviceId);
      refresh();
      onSuccess(res.points_earned);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '12px', padding: '14px', borderRadius: '10px', background: 'var(--accent-bg)', border: '1.5px solid var(--accent)' }}>
      <p style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '8px' }}>
        Enter OTP from pharmacist to claim points
      </p>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="number"
          maxLength={6}
          value={otp}
          onChange={(e) => { setOtp(e.target.value.slice(0, 6)); setError(''); }}
          placeholder="6-digit OTP"
          style={{
            flex: 1, padding: '10px 12px', borderRadius: '8px',
            border: `1.5px solid ${error ? '#ef4444' : 'var(--border-primary)'}`,
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '16px', fontWeight: '700', letterSpacing: '0.1em',
            outline: 'none',
          }}
        />
        <button
          onClick={handleClaim}
          disabled={loading || otp.length !== 6}
          style={{
            padding: '10px 16px', borderRadius: '8px',
            background: loading ? 'var(--bg-tertiary)' : 'var(--accent)',
            color: loading ? 'var(--text-tertiary)' : 'white',
            fontWeight: '700', fontSize: '13px',
            border: 'none', cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? '…' : 'Claim'}
        </button>
      </div>
      {error && (
        <p style={{ fontSize: '12px', color: '#ef4444', marginTop: '6px' }}>{error}</p>
      )}
    </div>
  );
}

function RequestCard({ req, onClaimed }) {
  const [expanded, setExpanded] = useState(false);
  const [claimed, setClaimed] = useState(false);
  const [pointsEarned, setPointsEarned] = useState(0);
  const status = STATUS_MAP[req.status] || STATUS_MAP.PENDING;
  const canClaim = req.status === 'OTP_GENERATED';
  const isBundle = req.items && req.items.length > 1;
  const reqLabel = req.req_number || `#${req.id?.slice(0, 8)}`;

  const handleSuccess = (pts) => {
    setClaimed(true);
    setPointsEarned(pts);
    onClaimed();
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1.5px solid var(--border-primary)',
      borderRadius: '14px',
      padding: '14px',
      marginBottom: '10px',
    }}>
      {/* Top row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* REQ number badge */}
          <div style={{ marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--accent)', fontFamily: 'monospace', background: 'var(--accent-bg)', padding: '2px 7px', borderRadius: '6px' }}>
              {reqLabel}
            </span>
            {isBundle && (
              <span style={{ marginLeft: '6px', fontSize: '10px', fontWeight: '600', padding: '2px 6px', borderRadius: '20px', background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                Bundle ×{req.items.length}
              </span>
            )}
          </div>
          <div style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {req.drug_name}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            {req.pharmacy_name || 'Unknown pharmacy'} · {timeAgo(req.created_at)}
          </div>
        </div>
        <span style={{
          fontSize: '11px', fontWeight: '700', padding: '3px 10px', borderRadius: '20px',
          background: status.bg, color: status.color, whiteSpace: 'nowrap', marginLeft: '8px',
        }}>
          {status.label}
        </span>
      </div>

      {/* Points row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
        <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
          {req.status === 'COMPLETED' ? 'Points earned' : 'Points pending'}
        </span>
        <span style={{ fontSize: '15px', fontWeight: '700', color: req.status === 'COMPLETED' ? '#16a34a' : 'var(--accent)' }}>
          {req.status === 'COMPLETED' ? '+' : '⏳ +'}{req.total_points} pts
        </span>
      </div>

      {/* Bundle items (expandable) */}
      {isBundle && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ marginTop: '10px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontSize: '12px', fontWeight: '600', padding: 0 }}
        >
          {expanded ? 'Hide' : 'Show'} {req.items.length} medicines ▾
        </button>
      )}
      {isBundle && expanded && (
        <div style={{ marginTop: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
          {req.items.map((item, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '3px 0', color: 'var(--text-secondary)' }}>
              <span>{item.drug_name} ({item.medicine_type}) ×{item.quantity}</span>
              <span style={{ color: 'var(--accent)', fontWeight: '600' }}>+{item.is_antibiotic ? 70 : 50}</span>
            </div>
          ))}
        </div>
      )}

      {/* OTP Entry */}
      {canClaim && !claimed && <OtpEntry request={req} onSuccess={handleSuccess} />}
      {claimed && (
        <div style={{ marginTop: '10px', padding: '10px 14px', borderRadius: '10px', background: 'rgba(22,163,74,0.1)', border: '1px solid rgba(22,163,74,0.3)', textAlign: 'center' }}>
          <span style={{ fontSize: '13px', fontWeight: '700', color: '#16a34a' }}>
            🎉 +{pointsEarned} pts credited!
          </span>
        </div>
      )}

      {/* Status help text */}
      {req.status === 'PENDING' && (
        <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '10px' }}>
          Waiting for pharmacy to accept your request.
        </p>
      )}
      {req.status === 'ACCEPTED' && (
        <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '10px' }}>
          Pharmacy accepted. Visit them with your medicines to get the OTP.
        </p>
      )}
    </div>
  );
}

export default function MyRequests() {
  const navigate = useNavigate();
  const { deviceId, refresh } = useRewards();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchRequests = useCallback(async () => {
    if (!deviceId) return;
    try {
      const res = await getUserRequests(deviceId);
      setRequests(res.requests || []);
    } catch {}
    setLoading(false);
  }, [deviceId]);

  useEffect(() => { fetchRequests(); }, [fetchRequests]);

  const pending = requests.filter(r => r.status !== 'COMPLETED');
  const completed = requests.filter(r => r.status === 'COMPLETED');

  return (
    <div className="page pb-24" style={{ maxWidth: '480px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            width: '36px', height: '36px', borderRadius: '10px',
            border: '1.5px solid var(--border-primary)',
            background: 'var(--bg-card)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', flexShrink: 0,
          }}
        >
          <Icons.ChevronLeft style={{ width: '18px', height: '18px', color: 'var(--text-secondary)' }} />
        </button>
        <div>
          <h1 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>My Take-Back Requests</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', margin: 0 }}>Enter OTP from pharmacist to claim points</p>
        </div>
        <button
          onClick={fetchRequests}
          style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', padding: '4px' }}
          title="Refresh"
        >
          <Icons.RefreshCw style={{ width: '18px', height: '18px' }} />
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-tertiary)' }}>
          <p style={{ fontSize: '14px' }}>Loading…</p>
        </div>
      ) : requests.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>📦</div>
          <p style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>No requests yet</p>
          <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', marginBottom: '20px' }}>Submit a take-back request to get started.</p>
          <button
            onClick={() => navigate('/takeback')}
            style={{
              padding: '12px 24px', borderRadius: '12px',
              background: 'var(--accent)', color: 'white',
              fontWeight: '700', fontSize: '14px', border: 'none', cursor: 'pointer',
            }}
          >
            Request Take-Back
          </button>
        </div>
      ) : (
        <>
          {pending.length > 0 && (
            <div>
              <p style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '10px' }}>
                Active ({pending.length})
              </p>
              {pending.map(r => (
                <RequestCard key={r.id} req={r} onClaimed={fetchRequests} />
              ))}
            </div>
          )}

          {completed.length > 0 && (
            <div style={{ marginTop: pending.length > 0 ? '20px' : 0 }}>
              <p style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '10px' }}>
                Completed ({completed.length})
              </p>
              {completed.map(r => (
                <RequestCard key={r.id} req={r} onClaimed={fetchRequests} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
