import React from 'react';

interface ProgressIndicatorProps {
  current: number;
  total: number;
  stage?: string;
  className?: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  current, 
  total, 
  stage = 'Processing', 
  className = ''
}) => {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className={`w-full space-y-2 ${className}`}>
      <div className="flex justify-between text-sm text-gray-600">
        <span>{stage}</span>
        <span>{percentage}% ({current}/{total})</span>
      </div>
      <div className="bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
        <div 
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export const LoadingSpinner: React.FC<{ message?: string }> = ({ 
  message = 'Processing...' 
}) => (
  <div className="flex flex-col items-center justify-center space-y-2">
    <div 
      className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"
    />
    <p className="text-sm text-gray-500">{message}</p>
  </div>
);

export const ErrorDisplay: React.FC<{ 
  message?: string, 
  onRetry?: () => void 
}> = ({ 
  message = 'An error occurred', 
  onRetry 
}) => (
  <div className="flex flex-col items-center justify-center space-y-2 p-4 bg-red-50 rounded-lg">
    <div className="text-red-500 text-lg font-semibold">
      {message}
    </div>
    {onRetry && (
      <button 
        onClick={onRetry}
        className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition"
      >
        Retry
      </button>
    )}
  </div>
);
