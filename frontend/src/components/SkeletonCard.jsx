export default function SkeletonCard({ lines = 3, className = '' }) {
  return (
    <div className={`card-surface p-4 space-y-3 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton h-4 rounded"
          style={{ width: `${85 - i * 15}%` }}
        />
      ))}
    </div>
  );
}
