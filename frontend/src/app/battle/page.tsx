'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { BattleState, executeMove, TurnResult } from '@/lib/api';
import PokemonCard from '@/components/PokemonCard';
import BattleLog from '@/components/BattleLog';

export default function BattlePage() {
  const [battleState, setBattleState] = useState<BattleState | null>(null);
  const [events, setEvents] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [gameOver, setGameOver] = useState<string | null>(null);
  const router = useRouter();
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const hitSoundRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const savedState = localStorage.getItem('initialBattleState');
    if (savedState) {
      const state = JSON.parse(savedState);
      setBattleState(state);
      setEvents([`A wild ${state.opponent_pokemon.name} appeared!`, `Go! ${state.player_pokemon.name}!`]);
      
      // Play cries
      if (state.opponent_pokemon.cry_url) {
        new Audio(state.opponent_pokemon.cry_url).play().catch(() => {});
      }
      setTimeout(() => {
        if (state.player_pokemon.cry_url) {
          new Audio(state.player_pokemon.cry_url).play().catch(() => {});
        }
      }, 1000);

      // Start background music
      audioRef.current = new Audio('/music/battle_music.mp3');
      audioRef.current.loop = true;
      audioRef.current.volume = 0.3;
      audioRef.current.play().catch(e => console.log('Audio autoplay blocked'));

      hitSoundRef.current = new Audio('/music/hit-sound.mp3');
    } else {
      router.push('/');
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, [router]);

  const handleMove = async (moveName: string) => {
    if (isProcessing || gameOver) return;
    setIsProcessing(true);
    
    try {
      const result: TurnResult = await executeMove(moveName);
      
      // Animate events one by one
      for (const eventObj of (result.turn_info.battle_events as any[])) {
        let message = '';
        
        if (eventObj.type === 'move') {
          message = `${eventObj.attacker_name} used ${eventObj.move}!`;
          if (eventObj.status_message) {
            // If there's a status message (like "but it failed"), we'll show it in the next step or append
          }
        } else if (eventObj.type === 'effectiveness') {
          message = eventObj.message;
        } else if (eventObj.type === 'status') {
          message = eventObj.message;
        } else if (eventObj.type === 'faint') {
          message = `${eventObj.pokemon_name} fainted!`;
        } else if (eventObj.message) {
          message = eventObj.message;
        }

        if (message) {
          setEvents(prev => [...prev, message]);
        }

        if (eventObj.type === 'move' && eventObj.status_message) {
           await new Promise(resolve => setTimeout(resolve, 500));
           setEvents(prev => [...prev, eventObj.status_message]);
        }
        
        if (eventObj.type === 'move' || eventObj.type === 'effectiveness') {
           hitSoundRef.current?.play();
        }
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      setBattleState(prev => prev ? {
        ...prev,
        player_pokemon: {
          ...prev.player_pokemon,
          current_hp: result.player_hp,
        },
        opponent_pokemon: {
          ...prev.opponent_pokemon,
          current_hp: result.opponent_hp,
        }
      } : null);

      if (result.is_game_over) {
        setGameOver(result.battle_result);
        setEvents(prev => [...prev, `Battle Over! ${result.battle_result}`]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!battleState) return <div className="min-h-screen bg-black flex items-center justify-center text-white font-mono animate-pulse">Loading Battle...</div>;

  return (
    <div className="min-h-screen bg-gray-950 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      <main className="container mx-auto px-4 py-8 h-screen flex flex-col justify-between relative z-10">
        {/* Opponent Side */}
        <div className="flex justify-end pr-8 md:pr-24">
          <PokemonCard
            name={battleState.opponent_pokemon.name}
            sprite={battleState.opponent_pokemon.sprite}
            currentHp={battleState.opponent_pokemon.current_hp}
            maxHp={battleState.opponent_pokemon.max_hp}
            level={100}
            types={battleState.opponent_pokemon.types}
            isOpponent
          />
        </div>

        {/* Player Side */}
        <div className="flex justify-start pl-8 md:pl-24">
          <PokemonCard
            name={battleState.player_pokemon.name}
            sprite={battleState.player_pokemon.sprite}
            currentHp={battleState.player_pokemon.current_hp}
            maxHp={battleState.player_pokemon.max_hp}
            level={100}
            types={battleState.player_pokemon.types}
          />
        </div>

        {/* UI Overlay */}
        <div className="w-full max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
          {/* Battle Log */}
          <div className="md:col-span-2">
            <BattleLog events={events} />
          </div>

          {/* Controls */}
          <div className="bg-gray-900/90 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col gap-4 shadow-2xl">
            {gameOver ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <h2 className="text-2xl font-bold text-yellow-500 uppercase tracking-widest">{gameOver}</h2>
                <button 
                  onClick={() => router.push('/')}
                  className="w-full py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all font-bold"
                >
                  NEW BATTLE
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-2">
                  {battleState.player_moves.map(move => (
                    <button
                      key={move.name}
                      onClick={() => handleMove(move.name)}
                      disabled={isProcessing || move.pp <= 0}
                      className={`p-3 rounded-xl border border-white/5 text-xs font-bold uppercase transition-all flex flex-col items-center gap-1
                        ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/10 active:scale-95'}
                        ${move.pp <= 0 ? 'bg-red-900/20 text-red-500' : 'bg-white/5'}
                      `}
                    >
                      <span>{move.name.replace('-', ' ')}</span>
                      <span className="text-[10px] opacity-50">{move.pp} / {move.max_pp} PP</span>
                    </button>
                  ))}
                </div>
                <button 
                  onClick={() => {
                    if (confirm('Forfeit battle?')) router.push('/');
                  }}
                  className="mt-2 text-xs text-gray-500 hover:text-red-400 transition-colors uppercase tracking-widest font-bold"
                >
                  Forfeit
                </button>
              </>
            )}
          </div>
        </div>
      </main>

      <style jsx global>{`
        @keyframes fade-in-down {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-down { animation: fade-in-down 0.8s ease-out; }
        .animate-fade-in-up { animation: fade-in-up 0.8s ease-out; }
        
        .type-fire { background-color: #EF4444; }
        .type-water { background-color: #3B82F6; }
        .type-grass { background-color: #10B981; }
        .type-electric { background-color: #F59E0B; }
        .type-psychic { background-color: #EC4899; }
        .type-ice { background-color: #60A5FA; }
        .type-dragon { background-color: #8B5CF6; }
        .type-dark { background-color: #374151; }
        .type-fairy { background-color: #F472B6; }
        .type-normal { background-color: #9CA3AF; }
        .type-fighting { background-color: #B91C1C; }
        .type-flying { background-color: #818CF8; }
        .type-poison { background-color: #8B5CF6; }
        .type-ground { background-color: #D97706; }
        .type-rock { background-color: #B45309; }
        .type-bug { background-color: #84CC16; }
        .type-ghost { background-color: #6366F1; }
        .type-steel { background-color: #64748B; }
      `}</style>
    </div>
  );
}
