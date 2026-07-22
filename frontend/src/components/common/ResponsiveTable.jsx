import React, { useState } from 'react';
import { useBreakpoint } from '../../config/breakpoints';
import { LayoutList, Table as TableIcon } from 'lucide-react';

/**
 * Enterprise Responsive Table Container
 * Supports sticky first column, horizontal scrolling shadows, and automatic Mobile Card Stack Mode.
 */
export default function ResponsiveTable({
  columns = [],
  data = [],
  keyExtractor = (item, idx) => item.id || idx,
  stickyFirstColumn = true,
  cardModeOnMobile = true,
  className = '',
  style = {}
}) {
  const { isMobile } = useBreakpoint();
  const [forceCardView, setForceCardView] = useState(false);

  const showCardView = isMobile && cardModeOnMobile || forceCardView;

  return (
    <div style={{ width: '100%', boxSizing: 'border-box', ...style }} className={className}>
      {/* View Toggle Bar on Mobile */}
      {isMobile && cardModeOnMobile && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
          <button
            onClick={() => setForceCardView((prev) => !prev)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-xs)',
              color: 'var(--color-text-secondary)',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            {showCardView ? <TableIcon size={14} /> : <LayoutList size={14} />}
            <span>{showCardView ? 'Show Table View' : 'Show Card View'}</span>
          </button>
        </div>
      )}

      {showCardView ? (
        /* Mobile Card Mode Stack */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {data.map((row, rowIdx) => (
            <div
              key={keyExtractor(row, rowIdx)}
              className="glass-panel"
              style={{
                padding: 'var(--card-padding)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}
            >
              {columns.map((col, colIdx) => (
                <div
                  key={colIdx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '4px 0',
                    borderBottom: colIdx < columns.length - 1 ? '1px solid var(--color-border-subtle)' : 'none'
                  }}
                >
                  <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', fontWeight: '600' }}>
                    {col.header}
                  </span>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)', textAlign: 'right' }}>
                    {col.render ? col.render(row, rowIdx) : row[col.accessor]}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      ) : (
        /* Horizontal Scrollable Table Container */
        <div
          style={{
            width: '100%',
            overflowX: 'auto',
            WebkitOverflowScrolling: 'touch',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-bg-card)'
          }}
        >
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.85rem',
              textAlign: 'left'
            }}
          >
            <thead>
              <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--color-border-subtle)' }}>
                {columns.map((col, idx) => (
                  <th
                    key={idx}
                    style={{
                      padding: '12px 16px',
                      color: 'var(--color-text-muted)',
                      fontWeight: '600',
                      fontSize: '0.75rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      whiteSpace: 'nowrap',
                      position: stickyFirstColumn && idx === 0 ? 'sticky' : 'static',
                      left: stickyFirstColumn && idx === 0 ? 0 : 'auto',
                      zIndex: stickyFirstColumn && idx === 0 ? 2 : 1,
                      background: stickyFirstColumn && idx === 0 ? 'var(--color-bg-surface)' : 'transparent',
                      boxShadow: stickyFirstColumn && idx === 0 ? '4px 0 10px rgba(0,0,0,0.3)' : 'none'
                    }}
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rowIdx) => (
                <tr
                  key={keyExtractor(row, rowIdx)}
                  style={{
                    borderBottom: rowIdx < data.length - 1 ? '1px solid var(--color-border-subtle)' : 'none',
                    transition: 'background 0.15s ease'
                  }}
                >
                  {columns.map((col, colIdx) => (
                    <td
                      key={colIdx}
                      style={{
                        padding: '12px 16px',
                        whiteSpace: 'nowrap',
                        color: 'var(--color-text-primary)',
                        position: stickyFirstColumn && colIdx === 0 ? 'sticky' : 'static',
                        left: stickyFirstColumn && colIdx === 0 ? 0 : 'auto',
                        zIndex: stickyFirstColumn && colIdx === 0 ? 1 : 0,
                        background: stickyFirstColumn && colIdx === 0 ? 'var(--color-bg-surface)' : 'transparent',
                        boxShadow: stickyFirstColumn && colIdx === 0 ? '4px 0 10px rgba(0,0,0,0.3)' : 'none'
                      }}
                    >
                      {col.render ? col.render(row, rowIdx) : row[col.accessor]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
