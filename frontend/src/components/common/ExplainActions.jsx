import React from 'react';

/**
 * Reusable action row for score cards.
 * Exposes:
 *  - Why? (ⓘ) -> Launches trust interpretation
 *  - Breakdown (📊) -> Launches score calculations, weights, and waterfalls
 *  - Methodology (📚) -> Launches visual pipeline, formula and references
 */
export default function ExplainActions({ scoreType, onAction }) {
  return (
    <div className="explain-actions-row" style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
      <button
        className="btn-explain-action"
        title="Why today's value exists and how to interpret it"
        style={{
          background: 'rgba(99, 102, 241, 0.05)',
          color: '#818cf8',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          padding: '6px 12px',
          fontSize: '12px',
          fontWeight: 600,
          borderRadius: '4px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          transition: 'all 0.2s ease',
        }}
        onClick={() => onAction(scoreType, 'why')}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(99, 102, 241, 0.15)';
          e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(99, 102, 241, 0.05)';
          e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.2)';
        }}
      >
        <span>ⓘ</span> Why?
      </button>

      <button
        className="btn-explain-action"
        title="View indicator values and contribution breakdown"
        style={{
          background: 'rgba(16, 185, 129, 0.05)',
          color: '#34d399',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          padding: '6px 12px',
          fontSize: '12px',
          fontWeight: 600,
          borderRadius: '4px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          transition: 'all 0.2s ease',
        }}
        onClick={() => onAction(scoreType, 'breakdown')}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(16, 185, 129, 0.15)';
          e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(16, 185, 129, 0.05)';
          e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        }}
      >
        <span>📊</span> Breakdown
      </button>

      <button
        className="btn-explain-action"
        title="View conceptual formula, factors, limits, and research references"
        style={{
          background: 'rgba(212, 168, 67, 0.05)',
          color: '#f43f5e',
          border: '1px solid rgba(212, 168, 67, 0.2)',
          padding: '6px 12px',
          fontSize: '12px',
          fontWeight: 600,
          borderRadius: '4px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          transition: 'all 0.2s ease',
        }}
        onClick={() => onAction(scoreType, 'methodology')}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(212, 168, 67, 0.15)';
          e.currentTarget.style.borderColor = 'rgba(212, 168, 67, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(212, 168, 67, 0.05)';
          e.currentTarget.style.borderColor = 'rgba(212, 168, 67, 0.2)';
        }}
      >
        <span>📚</span> Methodology
      </button>
    </div>
  );
}
