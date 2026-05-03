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
    <div 
      ref={scrollRef}
      className="bg-gray-900/90 backdrop-blur-md border border-white/10 rounded-2xl p-4 h-48 overflow-y-auto scroll-smooth flex flex-col gap-2 font-mono text-sm shadow-2xl"
    >
      {events.length === 0 ? (
        <p className="text-gray-500 animate-pulse italic">Waiting for battle actions...</p>
      ) : (
        events.map((event, i) => (
          <div 
            key={i} 
            className="text-gray-200 border-l-2 border-yellow-500 pl-3 py-1 bg-white/5 rounded-r-md animate-in slide-in-from-left duration-300"
          >
            {event}
          </div>
        ))
      )}
    </div>
  );
};

export default BattleLog;
