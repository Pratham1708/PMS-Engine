/**
 * Confidence color coding:
 *   80-100 → Green (high)
 *   60-80  → Yellow (medium)
 *   0-60   → Red (low)
 */
function getLevel(value) {
  if (value >= 80) return 'high';
  if (value >= 60) return 'medium';
  return 'low';
}

export default function ConfidenceBar({ value }) {
  const level = getLevel(value);

  return (
    <div className="confidence-bar-container">
      <div className="confidence-bar-track">
        <div
          className={`confidence-bar-fill ${level}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className={`confidence-value ${level}`}>
        {value.toFixed(1)}
      </span>
    </div>
  );
}
