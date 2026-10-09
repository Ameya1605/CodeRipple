import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  circle?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '16px',
  circle = false,
  className = '',
  style = {}
}) => {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius: circle ? '50%' : 'var(--radius-md)',
        ...style
      }}
    />
  );
};

interface SkeletonItemProps {
  count?: number;
  spacing?: string;
}

export const SkeletonLine: React.FC<SkeletonItemProps> = ({ count = 3, spacing = 'var(--space-md)' }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} height="16px" style={{ marginBottom: i < count - 1 ? spacing : 0 }} />
      ))}
    </>
  );
};

export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div
      className={`glass-panel ${className}`}
      style={{
        padding: 'var(--space-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-md)'
      }}
    >
      <Skeleton height="24px" width="60%" />
      <SkeletonLine count={3} />
      <Skeleton height="40px" width="30%" />
    </div>
  );
};
