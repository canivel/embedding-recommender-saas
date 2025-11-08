import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'danger' | 'warning' | 'info' | 'default';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', className = '' }) => {
  const variantClasses = {
    success: 'bg-green-100 text-green-800',
    danger: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
    default: 'bg-gray-100 text-gray-800',
  };

  return (
    <span
      className={`
        inline-flex items-center px-3 py-1
        rounded-full text-sm font-medium
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const variantMap: Record<string, 'success' | 'danger' | 'warning' | 'info' | 'default'> = {
    active: 'success',
    inactive: 'danger',
    suspended: 'warning',
    healthy: 'success',
    degraded: 'warning',
    unhealthy: 'danger',
    completed: 'success',
    failed: 'danger',
    running: 'info',
    queued: 'info',
  };

  return (
    <Badge variant={variantMap[status] || 'default'} className={className}>
      {status.replace(/_/g, ' ')}
    </Badge>
  );
};
