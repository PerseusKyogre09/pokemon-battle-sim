'use client';

import React from 'react';

interface PokeballProps {
  type: 'player' | 'opponent';
  visible: boolean;
}

const Pokeball: React.FC<PokeballProps> = ({ type, visible }) => {
  if (!visible) return null;

  return (
    <div className={`absolute z-50 ${
      type === 'player' ? 'left-12 bottom-16' : 'right-20 top-16'
    }`}>
      <img 
        src="/images/pokeball.png" 
        alt="Pokeball" 
        className={`w-12 h-12 object-contain ${
          type === 'player' ? 'animate-throw-player' : 'animate-throw-opponent'
        }`}
      />
    </div>
  );
};

export default Pokeball;
