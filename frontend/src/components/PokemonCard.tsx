'use client';

import React from 'react';
import HealthBar from './HealthBar';

interface PokemonCardProps {
  name: string;
  sprite: string;
  currentHp: number;
  maxHp: number;
  level: number;
  types: string[];
  isOpponent?: boolean;
  isVisible?: boolean;
  isAttacking?: boolean;
  isShaking?: boolean;
  isFainted?: boolean;
  showStatus?: boolean;
  layout?: 'sprite-only' | 'status-only' | 'full';
  flip?: boolean;
}

const PokemonCard: React.FC<PokemonCardProps> = ({ 
  name, sprite, currentHp, maxHp, level, types = [], 
  isOpponent, isVisible = true, isAttacking, isShaking, isFainted, showStatus = true,
  layout = 'full', flip = false
}) => {
  const renderSprite = () => (
    <div className={`relative group transition-all duration-500 flex flex-col items-center
      ${isVisible ? 'scale-100 opacity-100' : 'scale-0 opacity-0'}
      ${isAttacking ? (isOpponent ? '-translate-x-12 translate-y-12' : 'translate-x-12 -translate-y-12') : ''}
      ${isShaking ? 'animate-shake' : ''}
      ${isFainted ? 'animate-faint translate-y-40 opacity-0' : ''}
    `}>
      {/* GBA Battle Pod (Dark) */}
      <div className={`absolute bottom-2 left-1/2 -translate-x-1/2 w-48 h-12 rounded-[100%] blur-[2px] border-4 border-[#2d3a2d] bg-[#1a2e1a] shadow-[inset_0_4px_8px_rgba(0,0,0,0.4)] -z-0 opacity-80`} />
      
      <img 
        src={sprite} 
        alt={name} 
        className={`w-36 h-36 md:w-56 md:h-56 object-contain relative z-10 
          ${flip ? 'scale-x-[-1]' : ''}
          drop-shadow-lg
        `}
      />
    </div>
  );

  const renderStatus = () => (
    <div className={`w-64 gba-box gba-panel-shadow relative transition-all duration-500 overflow-hidden
      ${showStatus ? 'translate-x-0 opacity-100' : (isOpponent ? '-translate-x-20' : 'translate-x-20') + ' opacity-0'}
    `}
    style={{ 
      borderRadius: isOpponent ? '0 0 0 16px' : '16px 0 0 0',
      borderWidth: isOpponent ? '2px 0 4px 4px' : '4px 4px 2px 0'
    }}>
      <div className="flex justify-between items-center mb-1 border-b-2 border-white/10 pb-1">
        <h3 className="text-[10px] font-retro uppercase text-white flex items-center gap-1">
          {name}
          <span className="text-[8px] text-blue-400">♂</span>
        </h3>
        <div className="flex items-center gap-1">
          <span className="text-[8px] font-retro text-gray-400">Lv</span>
          <span className="text-[10px] font-retro text-white">{level}</span>
        </div>
      </div>
      
      <div className="mt-2 px-1">
        <HealthBar currentHp={currentHp} maxHp={maxHp} />
      </div>

      {!isOpponent && (
        <div className="flex justify-end items-center gap-2 mt-1">
          <div className="text-[8px] font-retro text-gray-300 whitespace-nowrap">
            {Math.max(0, Math.ceil(currentHp))}/{maxHp}
          </div>
        </div>
      )}
    </div>
  );

  if (layout === 'sprite-only') return renderSprite();
  if (layout === 'status-only') return renderStatus();

  return (
    <div className={`flex flex-col ${isOpponent ? 'items-end' : 'items-start'} gap-4 w-72 relative`}>
      {renderSprite()}
      {renderStatus()}
    </div>
  );
};

export default PokemonCard;
