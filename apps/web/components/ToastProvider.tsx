import React, { useContext } from 'react';
import { AnimatePresence } from 'framer-motion';
import ToastItem from './Toast';
import { NotificationContext } from '../../context/NotificationContext';

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const context = useContext(NotificationContext);

  if (!context) {
    return <>{children}</>;
  }

  const { toasts, removeToast } = context;

  return (
    <>
      {children}
      <div
        style={{
          position: 'fixed',
          top: 'var(--space-lg)',
          right: 'var(--space-lg)',
          zIndex: 'var(--z-tooltip)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-md)',
          pointerEvents: 'none'
        }}
      >
        <AnimatePresence mode="popLayout">
          {toasts.map(toast => (
            <div key={toast.id} style={{ pointerEvents: 'auto' }}>
              <ToastItem toast={toast} onClose={removeToast} />
            </div>
          ))}
        </AnimatePresence>
      </div>
    </>
  );
};
