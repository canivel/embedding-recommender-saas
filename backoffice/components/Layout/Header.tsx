'use client';

import React, { useEffect } from 'react';
import { useUIStore } from '@/lib/store';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';

export const Header: React.FC = () => {
  const { notifications, removeNotification } = useUIStore();

  useEffect(() => {
    const timers = notifications.map((notification) => {
      return setTimeout(() => {
        removeNotification(notification.id);
      }, 5000);
    });

    return () => timers.forEach(clearTimeout);
  }, [notifications, removeNotification]);

  const iconMap = {
    success: <CheckCircle className="w-5 h-5 text-green-600" />,
    error: <AlertCircle className="w-5 h-5 text-red-600" />,
    warning: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
    info: <Info className="w-5 h-5 text-blue-600" />,
  };

  const bgMap = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  };

  return (
    <div className="fixed top-0 right-0 z-40 p-4 max-w-md w-full space-y-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`flex items-start gap-3 p-4 rounded-lg border ${bgMap[notification.type]}`}
        >
          {iconMap[notification.type]}
          <p className="flex-1 text-sm font-medium text-gray-800">{notification.message}</p>
          <button
            onClick={() => removeNotification(notification.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={18} />
          </button>
        </div>
      ))}
    </div>
  );
};
