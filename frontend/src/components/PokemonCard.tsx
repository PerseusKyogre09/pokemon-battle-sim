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
}

const PokemonCard: React.FC<PokemonCardProps> = ({ 
  name, sprite, currentHp, maxHp, level, types = [], isOpponent 
}) => {
  return (
    <div className={`flex flex-col items-center ${isOpponent ? 'animate-fade-in-down' : 'animate-fade-in-up'}`}>
      <div className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
        <img 
          src={sprite} 
          alt={name} 
          className={`w-48 h-48 object-contain relative transition-transform duration-300 ${isOpponent ? 'hover:scale-110' : 'hover:scale-110 hover:-translate-y-2'}`}
        />
      </div>
      
      <div className="mt-4 w-64 bg-gray-900/80 backdrop-blur-md p-4 rounded-xl border border-white/10 shadow-2xl">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xl font-bold text-white uppercase tracking-wider">{name}</h2>
          <span className="text-yellow-400 font-mono">Lv.{level}</span>
        </div>
        
        <div className="flex gap-1 mb-3">
          {types.map(type => (
            <span 
              key={type} 
              className={`text-[10px] px-2 py-0.5 rounded-full text-white font-bold uppercase shadow-sm type-${type.toLowerCase()}`}
            >
              {type}
            </span>
          ))}
        </div>
        
        <HealthBar current={currentHp} max={maxHp} label="HP" />
      </div>
    </div>
  );
};

export default PokemonCard;
