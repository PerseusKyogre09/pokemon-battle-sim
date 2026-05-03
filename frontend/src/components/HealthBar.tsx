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
    if (percentage > 50) return 'var(--gba-hp-green)';
    if (percentage > 20) return 'var(--gba-hp-yellow)';
    return 'var(--gba-hp-red)';
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-1">
        <div className="text-[10px] font-retro text-[#f8d030] font-bold italic pr-1" style={{ textShadow: '1px 1px 0 #000' }}>
          {label}
        </div>
        <div className="flex-1 gba-hp-container h-[10px] relative">
          <div 
            className="h-full transition-all duration-1000 ease-out"
            style={{ 
              width: `${percentage}%`,
              backgroundColor: getStatusColor(),
              boxShadow: 'inset 0 2px 0 rgba(255,255,255,0.3), inset 0 -2px 0 rgba(0,0,0,0.1)'
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default HealthBar;
