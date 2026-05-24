import { useContext } from 'react';
import { NotificationContext } from '../context/NotificationContext';
import type { ToastType } from '../context/NotificationContext';

export const useNotification = () => {
  const context = useContext(NotificationContext);

  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }

  return {
    success: (message: string, duration?: number) => context.addToast(message, 'success', duration),
    error: (message: string, duration?: number) => context.addToast(message, 'error', duration),
    warning: (message: string, duration?: number) => context.addToast(message, 'warning', duration),
    info: (message: string, duration?: number) => context.addToast(message, 'info', duration),
    toast: (message: string, type: ToastType, duration?: number) => context.addToast(message, type, duration)
  };
};
