'use client';

import React from 'react';

interface HealthBarProps {
  currentHp: number;
  maxHp: number;
  label?: string;
}

const HealthBar: React.FC<HealthBarProps> = ({ currentHp, maxHp, label = 'HP' }) => {
  const percentage = Math.max(0, Math.min(100, (currentHp / maxHp) * 100));
  
  const getStatusColor = () => {
    if (percentage > 50) return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
    if (percentage > 20) return 'bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.5)]';
    return 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]';
  };

  return (
    <div className="w-full flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-retro text-yellow-400 drop-shadow-sm">{label}</span>
        <div className="flex-1 h-3 bg-black/40 border-2 border-gray-800 relative overflow-hidden" 
             style={{ clipPath: 'polygon(6px 0, 100% 0, 100% 100%, 0 100%, 0 6px)' }}>
          <div 
            className={`h-full transition-all duration-1000 ease-out ${getStatusColor()}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
      <div className="text-[8px] font-retro text-right text-white/70 tracking-tighter">
        {Math.ceil(currentHp)} / {maxHp}
      </div>
    </div>
  );
};

export default HealthBar;
