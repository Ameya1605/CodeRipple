import React from 'react';

export const LoadingSpinner: React.FC<{ size?: number, inline?: boolean }> = ({ size = 20, inline = false }) => {
  const style: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: '50%',
    border: '2px solid rgba(255,255,255,0.08)',
    borderTop: `2px solid var(--color-primary)`,
    animation: 'spin 1s linear infinite',
    display: inline ? 'inline-block' : 'block'
  };

  return <div style={style} aria-hidden="true" />;
};

export default LoadingSpinner;
