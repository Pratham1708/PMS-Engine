export default function GlassCard({
  children,
  className = '',
  hoverEffect = true,
  glow = false,
  style = {},
  onClick
}) {
  return (
    <div
      onClick={onClick}
      className={`glass-panel ${hoverEffect ? 'glass-panel-hover' : ''} ${glow ? 'glow-border' : ''} ${className}`}
      style={{
        padding: '20px',
        cursor: onClick ? 'pointer' : 'default',
        ...style
      }}
    >
      {children}
    </div>
  );
}
