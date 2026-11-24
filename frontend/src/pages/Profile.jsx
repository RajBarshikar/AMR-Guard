import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { useRewards } from '../contexts/RewardsContext';
import { getVoucherCatalog, getBadgeCatalog, redeemPoints, awardPoints, requestAuthOtp, verifyAuthOtp } from '../utils/api';
import Icons from '../components/Icons';

export default function Profile() {
  const { lang, setLang, t } = useLanguage();
  const { isDark, toggle } = useTheme();
  const { deviceId, rewards, refresh } = useRewards();
  const navigate = useNavigate();

  const [vouchers, setVouchers] = useState([]);
  const [badgeMeta, setBadgeMeta] = useState({});
  const [showRedeemModal, setShowRedeemModal] = useState(false);
  const [selectedVoucher, setSelectedVoucher] = useState(null);
  const [redeeming, setRedeeming] = useState(false);

  // OTP Login State
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [phoneStr, setPhoneStr] = useState('');
  const [otpStr, setOtpStr] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);

  useEffect(() => {
    getVoucherCatalog().then(res => setVouchers(res.vouchers || [])).catch(() => {});
    getBadgeCatalog().then(res => setBadgeMeta(res.badges || {})).catch(() => {});
  }, []);

  const handleRedeem = async () => {
    if (!selectedVoucher) return;
    setRedeeming(true);
    try {
      const res = await redeemPoints(deviceId, selectedVoucher.id);
      alert(`Redeemed! Your code: ${res.voucher_code}`);
      setShowRedeemModal(false);
      setSelectedVoucher(null);
      refresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setRedeeming(false);
    }
  };

  const handleBadgeClick = async (meta) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'AMR-Guard Achievement',
          text: `I just earned the ${meta.label} badge on AMR-Guard for safely disposing of medicines! Join me in fighting Antimicrobial Resistance.`,
          url: window.location.origin
        });
        await awardPoints(deviceId, 20, `Shared ${meta.label} badge on social media`);
        alert(`Shared successfully! You earned +20 points.`);
        refresh();
      } catch (err) {
        console.log('Share failed or cancelled:', err);
      }
    } else {
      alert(`I earned the ${meta.label} badge on AMR-Guard! (Sharing is not supported on this browser)`);
    }
  };

  const handleSendOtp = async () => {
    if (phoneStr.length < 10) { alert('Please enter a valid phone number'); return; }
    setLoginLoading(true);
    try {
      await requestAuthOtp(phoneStr);
      setOtpSent(true);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otpStr.length < 4) { alert('Please enter the OTP'); return; }
    setLoginLoading(true);
    try {
      await verifyAuthOtp(phoneStr, otpStr, deviceId);
      alert('Progress saved! Your device is now linked to your phone number.');
      setShowLoginModal(false);
      refresh();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoginLoading(false);
    }
  };

  const pts = rewards?.points || 0;
  const tier = rewards?.tier || 'Scout';
  const progressPct = rewards?.next_tier 
    ? Math.min(100, (pts / (pts + rewards.points_to_next_tier)) * 100)
    : 100;

  return (
    <div className="page pb-20">
      {/* Header */}
      <div className="text-center animate-fade-in-up">
        <div className="w-20 h-20 mx-auto rounded-full gradient-primary flex items-center justify-center mb-4" style={{ boxShadow: 'var(--shadow-accent)' }}>
          <Icons.ShieldCheck className="w-9 h-9 text-white" />
        </div>
        <h1 className="text-xl font-bold text-primary">
          {t(tier.toLowerCase().replace(' ', '_')) || tier}
        </h1>
        <p className="text-[13px] mt-1 text-tertiary">{t('guardian_level')}</p>
        <div className="flex items-center justify-center gap-1.5 mt-2">
          <Icons.Star className="w-4 h-4 text-yellow-500" />
          <span className="text-[13px] font-bold text-yellow-500">{pts} {t('points')}</span>
        </div>
      </div>

      {/* Tier Progress */}
      <div className="mt-6 animate-fade-in-up card p-4">
        <div className="flex justify-between text-[11px] mb-2 font-medium">
          <span className="text-primary">{tier}</span>
          <span className="text-tertiary">{rewards?.next_tier ? `Next: ${rewards.next_tier} (${rewards.points_to_next_tier} pts left)` : 'Max Tier'}</span>
        </div>
        <div className="w-full bg-secondary rounded-full h-2">
          <div className="bg-accent h-2 rounded-full transition-all duration-700" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      <div className="section-divider" />

      {/* Rewards Wallet */}
      <div className="animate-fade-in-up stagger-1">
        <div className="flex items-center justify-between mb-4">
          <p className="section-header !mb-0">{t('rewards_wallet')}</p>
          <button onClick={() => setShowRedeemModal(true)} className="text-[12px] font-bold text-accent px-3 py-1.5 rounded-lg bg-accent/10">
            {t('redeem_points')}
          </button>
        </div>
        <div className="grid grid-cols-1 gap-3">
          <div className="card p-4 flex flex-col items-center justify-center">
            <Icons.Star className="w-6 h-6 text-yellow-500 mb-1" />
            <span className="text-lg font-bold text-primary">{pts}</span>
            <span className="text-[10px] text-tertiary uppercase">{t('points')}</span>
          </div>
        </div>
      </div>

      <div className="section-divider" />

      {/* Badges Grid */}
      <div className="animate-fade-in-up stagger-2">
        <p className="section-header">{t('badges')}</p>
        {(!rewards?.badges || rewards.badges.length === 0) ? (
          <p className="text-[12px] text-tertiary text-center p-4 card">Complete actions to earn badges.</p>
        ) : (
          <div className="grid grid-cols-3 gap-3">
            {rewards.badges.map(bId => {
              const meta = badgeMeta[bId] || { label: bId, emoji: '🏅', color: '#94a3b8' };
              return (
                <div 
                  key={bId} 
                  onClick={() => handleBadgeClick(meta)}
                  className="card p-3 flex flex-col items-center text-center justify-center h-24 cursor-pointer hover:scale-105 transition-transform"
                >
                  <div className="text-2xl mb-1">{meta.emoji}</div>
                  <div className="text-[10px] font-bold leading-tight text-primary">{meta.label}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="section-divider" />

      {/* Transaction History */}
      <div className="animate-fade-in-up stagger-3">
        <p className="section-header">{t('transaction_history')}</p>
        {(!rewards?.transactions || rewards.transactions.length === 0) ? (
          <p className="text-[12px] text-tertiary text-center p-4 card">No transactions yet.</p>
        ) : (
          <div className="space-y-3">
            {rewards.transactions.slice(0, 5).map((tItem, i) => (
              <div key={i} className="card p-3 flex items-center justify-between">
                <div>
                  <p className="text-[12px] font-semibold text-primary">{tItem.reason}</p>
                  <p className="text-[10px] text-tertiary">{new Date(tItem.timestamp).toLocaleDateString()}</p>
                </div>
                <div className={`text-[13px] font-bold ${tItem.amount > 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {tItem.amount > 0 ? '+' : ''}{tItem.amount}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="section-divider" />

      {/* Settings */}
      <div className="animate-fade-in-up stagger-3">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <p className="section-header !mb-0">Settings</p>
          <button
            onClick={() => navigate('/my-requests')}
            className="text-[12px] font-bold text-accent px-3 py-1.5 rounded-lg"
            style={{ background: 'var(--accent-bg)' }}
          >
            My Requests ↗
          </button>
        </div>
        <div className="card p-5 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="icon-box w-10 h-10" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                {isDark ? <Icons.Moon className="w-4 h-4" /> : <Icons.Sun className="w-4 h-4" />}
              </div>
              <span className="text-[13px] font-medium text-primary">{isDark ? 'Dark Mode' : 'Light Mode'}</span>
            </div>
            <button onClick={toggle} className="w-12 h-7 rounded-full relative transition-colors duration-300"
                    style={{ background: isDark ? 'var(--accent)' : 'var(--bg-tertiary)' }}>
              <div className="absolute top-0.5 w-6 h-6 rounded-full shadow transition-transform duration-300"
                   style={{ background: 'white', transform: isDark ? 'translateX(22px)' : 'translateX(2px)' }} />
            </button>
          </div>
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="icon-box w-10 h-10" style={{ background: 'rgba(59,130,246,0.08)', color: '#3b82f6' }}>
                <Icons.Globe className="w-4 h-4" />
              </div>
              <span className="text-[13px] font-medium text-primary">{t('select_language')}</span>
            </div>
            <div className="flex gap-2">
              {[{ code: 'en', label: 'Eng' }, { code: 'mr', label: 'मराठी' }, { code: 'hi', label: 'हिंदी' }].map(({ code, label }) => (
                <button key={code} onClick={() => setLang(code)}
                        className={`flex-1 py-2 rounded-xl font-semibold text-[13px] transition-all duration-300 ${lang === code ? 'gradient-primary text-white' : 'card'}`}
                        style={lang === code ? { boxShadow: 'var(--shadow-accent)' } : { color: 'var(--text-secondary)' }}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="section-divider" />

      {/* Identity */}
      <div className="animate-fade-in-up stagger-3">
        <p className="section-header">Identity</p>
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="icon-box w-10 h-10" style={{ background: 'rgba(245,158,11,0.08)', color: '#d97706' }}>
                <Icons.Key className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[13px] font-medium text-primary">{rewards?.phone_number ? 'Linked Account' : t('device_token')}</p>
                <p className="text-[10px] mt-0.5 text-tertiary">{rewards?.phone_number || t('device_token_info')}</p>
              </div>
            </div>
            
            {!rewards?.phone_number && (
              <button 
                onClick={() => setShowLoginModal(true)}
                className="text-[12px] font-bold text-white px-3 py-1.5 rounded-lg bg-green-500"
              >
                Login to Save Progress
              </button>
            )}
          </div>
          <div className="px-3.5 py-3 rounded-xl text-[11px] font-mono truncate" style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)' }}>
            {deviceId}
          </div>
        </div>
      </div>

      {/* Redeem Modal */}
      {showRedeemModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-primary rounded-[8px] p-6 w-full max-w-sm max-h-[90vh] overflow-y-auto animate-fade-in-up shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-primary">Redeem Points</h2>
              <button onClick={() => setShowRedeemModal(false)} className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-secondary">
                <Icons.X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex justify-between items-center mb-6 bg-yellow-500/10 p-4 rounded-xl border border-yellow-500/20">
              <span className="font-semibold text-yellow-600">Your Balance</span>
              <span className="text-xl font-bold text-yellow-600">{pts} pts</span>
            </div>
            <div className="space-y-3 max-h-[50vh] overflow-y-auto">
              {vouchers.map(v => (
                <label key={v.id} className={`card p-4 flex items-center gap-4 cursor-pointer border-2 ${selectedVoucher?.id === v.id ? 'border-accent bg-accent/5' : 'border-transparent'}`}>
                  <input type="radio" className="hidden" checked={selectedVoucher?.id === v.id} onChange={() => setSelectedVoucher(v)} />
                  <div className="text-3xl">{v.emoji}</div>
                  <div className="flex-1">
                    <div className="font-bold text-[14px] text-primary">{v.label}</div>
                    <div className="text-[11px] text-tertiary leading-tight mt-0.5">{v.description}</div>
                  </div>
                  <div className={`font-bold text-[13px] ${pts >= v.points_required ? 'text-accent' : 'text-red-500'}`}>
                    {v.points_required} pts
                  </div>
                </label>
              ))}
            </div>
            <button 
              onClick={handleRedeem}
              disabled={!selectedVoucher || pts < selectedVoucher.points_required || redeeming}
              className="w-full btn-primary py-4 mt-6 text-[15px]"
            >
              {redeeming ? 'Redeeming...' : selectedVoucher ? (pts >= selectedVoucher.points_required ? 'Confirm Redeem' : 'Not Enough Points') : 'Select a Voucher'}
            </button>
          </div>
        </div>
      )}

      {/* Login / Save Progress Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-primary rounded-[8px] p-6 w-full max-w-sm max-h-[90vh] overflow-y-auto animate-fade-in-up shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-primary">Save Your Progress</h2>
              <button onClick={() => setShowLoginModal(false)} className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-secondary">
                <Icons.X className="w-4 h-4" />
              </button>
            </div>
            
            <p className="text-sm text-tertiary mb-6">
              Link your device to a phone number so you don't lose your points, rank, and badges if you clear your browser data or switch devices.
            </p>

            {!otpSent ? (
              <div>
                <label className="block text-[11px] font-bold text-tertiary uppercase mb-2 tracking-wider">Phone Number</label>
                <div className="flex items-center gap-2 mb-6">
                  <div className="px-4 py-3.5 rounded-[8px] border border-subtle bg-secondary text-primary font-bold text-[15px]">
                    +91
                  </div>
                  <input 
                    type="tel" 
                    placeholder="98765 43210" 
                    value={phoneStr}
                    maxLength={10}
                    onChange={(e) => setPhoneStr(e.target.value.replace(/\D/g, ''))}
                    className="w-full px-4 py-3.5 rounded-[8px] border border-subtle bg-secondary text-primary text-[15px] outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all tracking-wide"
                  />
                </div>
                <button 
                  onClick={handleSendOtp}
                  disabled={loginLoading || phoneStr.length < 10}
                  className="w-full py-3.5 rounded-[8px] text-[14px] font-bold bg-green-500 text-white disabled:bg-secondary disabled:text-tertiary disabled:border disabled:border-subtle"
                >
                  {loginLoading ? 'Sending OTP...' : 'Send OTP'}
                </button>
              </div>
            ) : (
              <div>
                <label className="block text-[11px] font-bold text-tertiary uppercase mb-2 tracking-wider">Enter OTP</label>
                <input 
                  type="text" 
                  placeholder="1 2 3 4 5 6" 
                  value={otpStr}
                  maxLength={6}
                  onChange={(e) => setOtpStr(e.target.value.replace(/\D/g, ''))}
                  className="w-full p-4 rounded-[8px] border border-subtle bg-secondary text-primary tracking-[0.5em] font-bold text-center text-lg outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all mb-6"
                />
                <button 
                  onClick={handleVerifyOtp}
                  disabled={loginLoading || otpStr.length < 4}
                  className="w-full py-3.5 rounded-[8px] text-[14px] font-bold bg-green-500 text-white disabled:bg-secondary disabled:text-tertiary disabled:border disabled:border-subtle"
                >
                  {loginLoading ? 'Verifying...' : 'Verify & Save Progress'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 text-center pb-2">
        <p className="text-[11px] font-medium text-tertiary">AMR-Guard v2.0</p>
      </div>
    </div>
  );
}
