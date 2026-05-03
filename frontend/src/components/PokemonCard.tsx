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
    <div className={`relative group transition-all duration-500
      ${isVisible ? 'scale-100 opacity-100' : 'scale-0 opacity-0'}
      ${isAttacking ? (isOpponent ? '-translate-x-12 translate-y-12' : 'translate-x-12 -translate-y-12') : ''}
      ${isShaking ? 'animate-shake' : ''}
      ${isFainted ? 'animate-faint translate-y-40 opacity-0' : ''}
    `}>
      <div className={`absolute inset-0 bg-white/5 rounded-full blur-3xl transition-all duration-500 group-hover:bg-white/10`} />
      <img 
        src={sprite} 
        alt={name} 
        className={`w-36 h-36 md:w-48 md:h-48 object-contain relative z-10 transition-transform duration-300 hover:scale-105 drop-shadow-[0_15px_15px_rgba(0,0,0,0.6)]
          ${flip ? 'scale-x-[-1]' : ''}
        `}
      />
      <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-28 h-5 bg-black/40 rounded-full blur-md -z-0" />
    </div>
  );

  const renderStatus = () => (
    <div className={`w-72 bg-gray-900/90 backdrop-blur-md border-4 border-gray-800 p-4 shadow-2xl relative transition-all duration-500
      ${showStatus ? 'translate-x-0 opacity-100' : (isOpponent ? '-translate-x-20' : 'translate-x-20') + ' opacity-0'}
      ${isOpponent ? 'rounded-r-2xl' : 'rounded-l-2xl'}
    `}
    style={{ clipPath: isOpponent ? 'polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 0 100%)' : 'polygon(15px 0, 100% 0, 100% 100%, 0 100%, 0 15px)' }}>
      <div className="flex justify-between items-end mb-2">
        <h3 className="text-xs font-retro uppercase tracking-tighter text-white truncate max-w-[140px]">{name}</h3>
        <span className="text-[10px] font-retro text-gray-400">Lv{level}</span>
      </div>
      
      <div className="flex gap-1 mb-4">
        {types.map(type => (
          <span 
            key={type} 
            className={`text-[8px] font-retro px-1.5 py-0.5 rounded-sm uppercase text-white shadow-sm type-${type.toLowerCase()}`}
          >
            {type}
          </span>
        ))}
      </div>

      <HealthBar currentHp={currentHp} maxHp={maxHp} />
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
