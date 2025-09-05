import React from 'react';

interface LoadingProps {
  type?: 'spinner' | 'dots' | 'skeleton';
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'purple' | 'gray';
}

const Loading: React.FC<LoadingProps> = ({ type = 'spinner', size = 'md', color = 'blue' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  const colorClasses = {
    blue: 'text-blue-600',
    purple: 'text-purple-600',
    gray: 'text-gray-600'
  };

  if (type === 'dots') {
    return (
      <div className="flex space-x-1">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full bg-current animate-pulse`}
            style={{ animationDelay: `${i * 0.2}s` }}
          />
        ))}
      </div>
    );
  }

  if (type === 'skeleton') {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  return (
    <div
      className={`${sizeClasses[size]} ${colorClasses[color]} animate-spin border-2 border-current border-t-transparent rounded-full`}
    />
  );
};

export default Loading;