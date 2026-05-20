import { useState, useEffect } from 'react';

const universalTips = [
  { text: "94% of Maharashtra households throw expired medicines in the trash. That's how antibiotics enter our water supply and create drug-resistant bacteria." },
  { text: "96.5% of people said they would return medicines if a take-back program existed. You're already ahead of the curve." },
  { text: "Only 1 in 5 people in Maharashtra know what Antimicrobial Resistance (AMR) is. By using this app, you're part of the solution." },
  { text: "Pharmacists agree — returning unused medicines to a pharmacy is the single most effective way to prevent antibiotic pollution." },
  { text: "Expired antibiotics don't just become ineffective — they break down into compounds that teach bacteria how to survive future treatments." }
];

const districtTips = {
  "Satara": [
    { text: "Taking antibiotics without a doctor's prescription is one of the leading drivers of drug resistance in rural Maharashtra. Always consult a doctor first." },
    { text: "Stopping antibiotics when you feel better leaves the strongest bacteria alive — they survive and multiply. Always complete the full course." }
  ],
  "Gadchiroli": [
    { text: "Using leftover antibiotics for a new illness without a prescription can do more harm than good — the bacteria causing your new illness may be completely different." },
    { text: "In Gadchiroli, more than half of households store unused antibiotics for future use. Leftover medicines are best returned, not stored." }
  ],
  "Raigad": [
    { text: "Antibiotics don't work on viral infections like the common cold or flu. Using them anyway builds resistance without any benefit." }
  ]
};

export default function LoadingTips({ district, title = "Analyzing..." }) {
  const [tipIndex, setTipIndex] = useState(0);
  const [pool, setPool] = useState([]);

  useEffect(() => {
    const combinedPool = [...universalTips, ...(districtTips[district] || [])];
    // Shuffle the pool for variety
    const shuffled = combinedPool.sort(() => 0.5 - Math.random());
    setPool(shuffled);
  }, [district]);

  useEffect(() => {
    if (pool.length === 0) return;
    const interval = setInterval(() => {
      setTipIndex(prev => (prev + 1) % pool.length);
    }, 4500);
    return () => clearInterval(interval);
  }, [pool]);

  if (pool.length === 0) return null;

  return (
    <div className="flex flex-col items-center justify-center text-center p-6" style={{ minHeight: '60vh' }}>
      <div className="w-12 h-12 rounded-full border-[3px] border-t-transparent animate-spin mb-6" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
      
      <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>{title}</h3>
      
      <div 
        className="w-full max-w-sm rounded-2xl p-5 shadow-lg relative overflow-hidden transition-opacity duration-500"
        style={{ 
          background: 'var(--bg-card)', 
          border: '1px solid var(--border-primary)',
          boxShadow: 'var(--shadow-lg)'
        }}
      >
        <div className="flex items-center gap-2 mb-3 justify-center">
          <span style={{ fontSize: '16px' }}>💡</span>
          <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {district ? `${district} Insights` : 'Did you know?'}
          </span>
        </div>
        <p key={tipIndex} className="animate-fade-in text-sm font-medium leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          "{pool[tipIndex].text}"
        </p>
      </div>
      
      {/* Skeleton bar to indicate loading progress visually */}
      <div className="mt-8 w-48 h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
        <div className="h-full bg-gradient-to-r from-transparent via-teal-400 to-transparent animate-scan-line w-1/2" />
      </div>
    </div>
  );
}
