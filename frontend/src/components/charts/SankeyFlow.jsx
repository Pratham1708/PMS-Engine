import React from 'react';

/**
 * Premium SVG-based Sankey-style decision flow chart.
 * Illustrates inputs (Technical, ML, GRU, Reliability) flowing via weighted paths
 * into the Dynamic Weight Optimizer and out to the Composite Score.
 */
export default function SankeyFlow({
  tech = 0.0,
  ml = 0.0,
  gru = 0.0,
  reliability = 70.0,
  wTech = 0.40,
  wMl = 0.35,
  wGru = 0.15,
  wReliability = 0.10,
  composite = 0.0,
  title = "Composite Weight Allocation Journey"
}) {
  // SVG coordinates: Width 600, Height 260
  const width = 600;
  const height = 260;

  // Source nodes coordinates (X = 30)
  const sources = [
    { name: 'Technical Score', value: tech, weight: wTech, y: 30, color: '#38bdf8' },
    { name: 'Ensemble ML Score', value: ml, weight: wMl, y: 90, color: '#34d399' },
    { name: 'GRU Recurrent Score', value: gru, weight: wGru, y: 150, color: '#a78bfa' },
    { name: 'Reliability Index', value: reliability, weight: wReliability, y: 210, color: '#f43f5e' }
  ];

  // Target node coordinates (X = 300, Y = 120) - Optimizer
  // Output node coordinates (X = 520, Y = 120) - Composite Score
  const optX = 290;
  const optY = 120;
  const outX = 520;
  const outY = 120;

  const scoreClass = (val) => val > 0 ? '#10b981' : val < 0 ? '#ef4444' : '#9ca3af';

  return (
    <div className="sankey-flow-chart" style={{ width: '100%', overflowX: 'auto', background: 'rgba(5, 10, 20, 0.3)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
      {title && (
        <h5 style={{ margin: '0 0 16px 0', color: '#fff', fontSize: '14px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>📊</span> {title}
        </h5>
      )}
      
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%" style={{ overflow: 'visible' }}>
        <defs>
          {/* Neon Glow Filter */}
          <filter id="glow" x="-10%" y="-10%" width="120%" height="120%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          
          {/* Path Gradients */}
          {sources.map((src, idx) => (
            <linearGradient id={`grad-${idx}`} x1="0%" y1="0%" x2="100%" y2="0%" key={idx}>
              <stop offset="0%" stopColor={src.color} stopOpacity="0.8" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0.4" />
            </linearGradient>
          ))}
          <linearGradient id="grad-out" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#818cf8" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="1" />
          </linearGradient>
        </defs>

        {/* Weighted Flow Paths from Sources to Optimizer */}
        {sources.map((src, idx) => {
          // Bezier curve control points
          const pathD = `M 130 ${src.y} C ${(optX + 130) / 2} ${src.y}, ${(optX + 130) / 2} ${optY + 15}, ${optX} ${optY + 15}`;
          const strokeWidth = Math.max(src.weight * 25, 2); // Map weight to path thickness
          return (
            <g key={idx}>
              {/* Glow trace */}
              <path
                d={pathD}
                fill="none"
                stroke={src.color}
                strokeWidth={strokeWidth}
                opacity="0.1"
              />
              {/* Actual flow path */}
              <path
                d={pathD}
                fill="none"
                stroke={`url(#grad-${idx})`}
                strokeWidth={strokeWidth}
                opacity="0.75"
                style={{
                  strokeDasharray: '400',
                  strokeDashoffset: '0',
                  animation: 'dash 10s linear infinite'
                }}
              />
              {/* Path weight percentage tooltip marker */}
              <text
                x={(optX + 130) / 2}
                y={src.y + (optY + 15 - src.y) * 0.4 - 5}
                fill="#94a3b8"
                fontSize="10px"
                textAnchor="middle"
                fontWeight="bold"
              >
                {Math.round(src.weight * 100)}%
              </text>
            </g>
          );
        })}

        {/* Flow Path from Optimizer to Composite Score */}
        <path
          d={`M ${optX + 100} ${optY + 15} L ${outX} ${outY + 15}`}
          fill="none"
          stroke="url(#grad-out)"
          strokeWidth="8"
          opacity="0.85"
        />

        {/* 1. Source Nodes (Left) */}
        {sources.map((src, idx) => (
          <g key={idx} transform={`translate(10, ${src.y - 18})`}>
            {/* Box */}
            <rect
              width="120"
              height="36"
              rx="4"
              fill="rgba(10, 22, 40, 0.9)"
              stroke={src.color}
              strokeWidth="1.5"
            />
            {/* Ticker Name */}
            <text x="8" y="15" fill="#e2e8f0" fontSize="10px" fontWeight="bold">
              {src.name}
            </text>
            {/* Value */}
            <text x="8" y="28" fill={src.color} fontSize="11px" fontWeight="900">
              {src.value > 0 && idx < 3 ? '+' : ''}{src.value.toFixed(2)}
            </text>
          </g>
        ))}

        {/* 2. Dynamic Weight Optimizer Node (Center) */}
        <g transform={`translate(${optX}, ${optY - 20})`} filter="url(#glow)">
          <rect
            width="110"
            height="70"
            rx="6"
            fill="rgba(99, 102, 241, 0.2)"
            stroke="#818cf8"
            strokeWidth="2"
          />
          <text x="55" y="24" fill="#fff" fontSize="9px" fontWeight="900" textAnchor="middle">
            DYNAMIC WEIGHT
          </text>
          <text x="55" y="38" fill="#fff" fontSize="9px" fontWeight="900" textAnchor="middle">
            OPTIMIZER
          </text>
          <rect
            x="10"
            y="48"
            width="90"
            height="14"
            rx="2"
            fill="rgba(5, 10, 20, 0.8)"
          />
          <text x="55" y="58" fill="#a5b4fc" fontSize="8px" fontWeight="bold" textAnchor="middle">
            Regime: Balanced
          </text>
        </g>

        {/* 3. Output Node (Right) */}
        <g transform={`translate(${outX}, ${outY - 12})`} filter="url(#glow)">
          <rect
            width="75"
            height="55"
            rx="6"
            fill="rgba(16, 185, 129, 0.15)"
            stroke="#10b981"
            strokeWidth="2"
          />
          <text x="37.5" y="18" fill="#e2e8f0" fontSize="9px" fontWeight="bold" textAnchor="middle">
            COMPOSITE
          </text>
          <text x="37.5" y="28" fill="#e2e8f0" fontSize="9px" fontWeight="bold" textAnchor="middle">
            SCORE
          </text>
          <text x="37.5" y="46" fill={scoreClass(composite)} fontSize="14px" fontWeight="900" textAnchor="middle">
            {composite > 0 ? '+' : ''}{composite.toFixed(2)}
          </text>
        </g>
      </svg>
      
      {/* Legend / Guide */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '10px', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px' }}>
        <span>Scale: Weights map to line thickness.</span>
        <span>Color guide: input scores flow from left (inputs) through optimized weights to final composite score (right).</span>
      </div>
    </div>
  );
}
