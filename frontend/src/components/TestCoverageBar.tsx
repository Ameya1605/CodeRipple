
interface TestCoverageBarProps {
  percentage: number;
  className?: string;
  label?: string;
}

export const TestCoverageBar: React.FC<TestCoverageBarProps> = ({ percentage, className = '', label }) => {
  const pct = Math.max(0, Math.min(100, percentage));
  
  return (
    <div className={`test-coverage-bar-container ${className}`} style={{ width: '100%' }}>
      <div style={{ flex: 1 }}>
        {label && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6, fontWeight: 500 }}>{label}</div>}
        <div className="test-coverage-bar">
          <div 
            className="test-coverage-bar-fill" 
            style={{ 
              width: `${pct}%`,
              background: pct < 50 ? 'var(--tier-critical)' : pct < 80 ? 'var(--tier-high)' : 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))'
            }}
          />
        </div>
      </div>
      <span className="coverage-text" style={{ 
        color: pct < 50 ? 'var(--tier-critical)' : pct < 80 ? 'var(--tier-high)' : 'var(--text-primary)',
        marginTop: label ? 18 : 0
      }}>
        {pct.toFixed(0)}%
      </span>
    </div>
  );
};
