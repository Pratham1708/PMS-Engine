/**
 * Horizontal score bar for -100 to +100 range scores.
 * Center line at 0. Positive fills right (green), negative fills left (red).
 */
export default function ScoreBar({ label, value, min = -100, max = 100 }) {
  const absMax = Math.max(Math.abs(min), Math.abs(max));
  const isPositive = value >= 0;
  const pct = Math.min(Math.abs(value) / absMax * 50, 50);

  const fillStyle = isPositive
    ? { left: '50%', width: `${pct}%` }
    : { left: `${50 - pct}%`, width: `${pct}%` };

  const valClass = value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';

  return (
    <div className="score-bar-container">
      <div className="score-bar-header">
        <span className="score-bar-label">{label}</span>
        <span className={`score-bar-value ${valClass}`}>
          {value > 0 ? '+' : ''}{value.toFixed(2)}
        </span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-center" />
        <div
          className={`score-bar-fill ${isPositive ? 'positive' : 'negative'}`}
          style={fillStyle}
        />
      </div>
    </div>
  );
}
