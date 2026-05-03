'use client';

import React, { useEffect, useRef } from 'react';

interface BattleLogProps {
  events: string[];
}

const BattleLog: React.FC<BattleLogProps> = ({ events }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="flex flex-col h-40 md:h-48">
      <div className="bg-gray-900/90 backdrop-blur-md border-4 border-gray-800 rounded-2xl p-4 h-full relative shadow-inner">
        {/* Retro scanline effect overlay */}
        <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(255,0,0,0.02),rgba(0,255,0,0.01),rgba(0,0,255,0.02))] bg-[length:100%_2px,3px_100%] z-20" />
        
        <div 
          ref={scrollRef}
          className="h-full overflow-y-auto space-y-2 scroll-smooth pr-2 custom-scrollbar relative z-10"
        >
          {events.length === 0 ? (
            <p className="text-gray-500 font-retro text-xs animate-pulse">Waiting for battle actions...</p>
          ) : (
            events.map((event, i) => (
              <div 
                key={i} 
                className={`font-retro text-[10px] leading-relaxed animate-in fade-in slide-in-from-left-2 duration-300
                  ${event.includes('Critical') ? 'text-red-400 font-bold' : 
                    event.includes('effective') ? 'text-yellow-400' : 
                    event.includes('fainted') ? 'text-gray-400 italic' : 'text-gray-100'}
                `}
              >
                <span className="text-white/30 mr-2">{'>'}</span>
                {event}
              </div>
            ))
          )}
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(0,0,0,0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #4b5563;
          border-radius: 10px;
        }
      `}</style>
    </div>
  );
};

export default BattleLog;
