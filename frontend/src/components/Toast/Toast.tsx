import React from 'react';
import { motion } from 'framer-motion';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import type { Toast as ToastDef, ToastType } from '../../context/NotificationContext';

interface ToastProps {
  toast: ToastDef;
  onClose: (id: string) => void;
}

const getToastConfig = (type: ToastType) => {
  const configs = {
    success: {
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.3)',
      icon: CheckCircle,
      color: '#10b981'
    },
    error: {
      bg: 'rgba(239, 68, 68, 0.1)',
      border: 'rgba(239, 68, 68, 0.3)',
      icon: AlertCircle,
      color: '#ef4444'
    },
    warning: {
      bg: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.3)',
      icon: AlertTriangle,
      color: '#f59e0b'
    },
    info: {
      bg: 'rgba(59, 130, 246, 0.1)',
      border: 'rgba(59, 130, 246, 0.3)',
      icon: Info,
      color: '#3b82f6'
    }
  };
  return configs[type];
};

export const ToastItem: React.FC<ToastProps> = ({ toast, onClose }) => {
  const config = getToastConfig(toast.type);
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, x: 20 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      exit={{ opacity: 0, y: -20, x: 20 }}
      transition={{ duration: 0.3 }}
      style={{
        background: config.bg,
        borderColor: config.border,
        borderWidth: '1px',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-md)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-md)',
        boxShadow: 'var(--shadow-md)',
        maxWidth: '400px'
      }}
    >
      <Icon size={20} color={config.color} style={{ flexShrink: 0 }} />
      <span style={{ color: 'var(--text-primary)', fontSize: '14px', flex: 1 }}>
        {toast.message}
      </span>
      <button
        onClick={() => onClose(toast.id)}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--text-tertiary)',
          padding: 0,
          display: 'flex',
          alignItems: 'center',
          transition: 'color var(--duration-200) var(--timing-in-out)'
        }}
        onMouseEnter={e => e.currentTarget.style.color = config.color}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-tertiary)'}
      >
        <X size={16} />
      </button>
    </motion.div>
  );
};

export default ToastItem;
