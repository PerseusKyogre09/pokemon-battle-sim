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
    <div className="flex flex-col h-32">
      <div className="bg-[#0f172a] border-[6px] border-[#475569] rounded-xl p-4 h-full relative shadow-[inset_0_4px_0_#1e293b,inset_0_-4px_0_#020617] flex items-center">
        {/* Inner subtle border effect */}
        <div className="absolute inset-1 border-2 border-[#1e293b] rounded-lg pointer-events-none" />
        
        <div 
          ref={scrollRef}
          className="h-full w-full overflow-y-auto space-y-3 scroll-smooth pr-2 custom-scrollbar relative z-10 py-2"
        >
          {events.length === 0 ? (
            <p className="text-gray-500 font-retro text-[10px] uppercase">Waiting for battle actions...</p>
          ) : (
            events.map((event, i) => (
              <div 
                key={i} 
                className={`font-retro text-[12px] leading-relaxed animate-in fade-in slide-in-from-left-2 duration-300 uppercase text-gray-200`}
              >
                {event}
              </div>
            ))
          )}
        </div>
        
        {/* Blinking triangle cursor when events exist */}
        {events.length > 0 && (
          <div className="absolute bottom-4 right-4 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[10px] border-t-red-500 animate-bounce" />
        )}
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 0px;
        }
      `}</style>
    </div>
  );
};

export default BattleLog;
