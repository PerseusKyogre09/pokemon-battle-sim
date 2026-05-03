import React from 'react';

interface HealthBarProps {
  current: number;
  max: number;
  label: string;
}

const HealthBar: React.FC<HealthBarProps> = ({ current, max, label }) => {
  const percentage = Math.max(0, (current / max) * 100);
  
  const getColor = () => {
    if (percentage > 50) return 'bg-green-500';
    if (percentage > 20) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden border border-gray-700 shadow-inner relative">
      <div 
        className={`h-full transition-all duration-500 ease-out ${getColor()}`}
        style={{ width: `${percentage}%` }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent pointer-events-none" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[10px] font-bold text-white drop-shadow-md">
          {label}: {current} / {max}
        </span>
      </div>
    </div>
  );
};

export default HealthBar;
