'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { BattleState, executeMove, TurnResult } from '@/lib/api';
import PokemonCard from '@/components/PokemonCard';
import BattleLog from '@/components/BattleLog';
import Pokeball from '@/components/Pokeball';

type BattleStage = 'intro-opponent' | 'intro-player' | 'active' | 'gameover';

// Utility to get signed URL for audio
const getAudioUrl = async (filename: string) => {
  try {
    // Determine base URL (strip /api if needed)
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7860/api';
    const baseUrl = apiBase.endsWith('/api') ? apiBase.replace(/\/api$/, '') : apiBase;
    
    const response = await fetch(`${baseUrl}/api/audio/signed-url/${filename}`);
    const data = await response.json();
    console.log(`🎵 Audio [${data.source}]: ${filename} -> ${data.url}`);
    return data.url;
  } catch (error) {
    console.error(`Error fetching signed URL for ${filename}:`, error);
    return `/music/${filename}`; // Fallback to local public folder
  }
};

export default function BattlePage() {
  const [battleState, setBattleState] = useState<BattleState | null>(null);
  const [events, setEvents] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [gameOver, setGameOver] = useState<string | null>(null);
  const [battleStage, setBattleStage] = useState<BattleStage>('intro-opponent');
  
  // Animation states for cards
  const [playerAnim, setPlayerAnim] = useState({ visible: false, status: false, attacking: false, shaking: false, fainted: false });
  const [opponentAnim, setOpponentAnim] = useState({ visible: false, status: false, attacking: false, shaking: false, fainted: false });
  const [pokeballState, setPokeballState] = useState({ player: false, opponent: false });
  const [showFlash, setShowFlash] = useState(false);
  const [showStartOverlay, setShowStartOverlay] = useState(true);
  const [hoveredMove, setHoveredMove] = useState<any>(null);

  const router = useRouter();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const hitSoundRef = useRef<HTMLAudioElement | null>(null);
  const pokeballSoundRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const savedState = localStorage.getItem('initialBattleState');
    if (savedState) {
      const state = JSON.parse(savedState);
      setBattleState(state);
      setupAudio();
    } else {
      router.push('/');
    }

    return () => {
      if (audioRef.current) audioRef.current.pause();
    };
  }, [router]);

  const setupAudio = async () => {
    const battleMusicUrl = await getAudioUrl('battle-music.mp3');
    const hitSoundUrl = await getAudioUrl('hit-sound.mp3');
    const pokeballSoundUrl = await getAudioUrl('pokeball-throw.mp3');

    audioRef.current = new Audio(battleMusicUrl);
    audioRef.current.loop = true;
    audioRef.current.volume = 0.3;
    
    hitSoundRef.current = new Audio(hitSoundUrl);
    pokeballSoundRef.current = new Audio(pokeballSoundUrl);
  };

  const handleStartBattle = () => {
    if (!battleState) return;
    setShowStartOverlay(false);
    startIntroSequence(battleState);
  };

  const startIntroSequence = async (state: BattleState) => {
    // Wait for audio to be ready
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 1. Music starts
    audioRef.current?.play().catch(() => console.log('Autoplay blocked'));
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 2. Opponent Throw
    setPokeballState({ player: false, opponent: true });
    pokeballSoundRef.current?.play().catch(() => {});
    setEvents([`A wild ${state.opponent_pokemon.name} appeared!`]);
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 3. Opponent Flash & Appear
    setPokeballState({ player: false, opponent: false });
    setShowFlash(true);
    setTimeout(() => setShowFlash(false), 300);
    setOpponentAnim(prev => ({ ...prev, visible: true }));
    
    if (state.opponent_pokemon.cry_url) {
      new Audio(state.opponent_pokemon.cry_url).play().catch(() => {});
    }
    
    await new Promise(resolve => setTimeout(resolve, 800));
    setOpponentAnim(prev => ({ ...prev, status: true }));
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 4. Player Throw
    setBattleStage('intro-player');
    setPokeballState({ player: true, opponent: false });
    pokeballSoundRef.current?.play().catch(() => {});
    setEvents(prev => [...prev, `Go! ${state.player_pokemon.name}!`]);
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 5. Player Flash & Appear
    setPokeballState({ player: false, opponent: false });
    setShowFlash(true);
    setTimeout(() => setShowFlash(false), 300);
    setPlayerAnim(prev => ({ ...prev, visible: true }));
    
    if (state.player_pokemon.cry_url) {
      new Audio(state.player_pokemon.cry_url).play().catch(() => {});
    }
    
    await new Promise(resolve => setTimeout(resolve, 800));
    setPlayerAnim(prev => ({ ...prev, status: true }));
    
    await new Promise(resolve => setTimeout(resolve, 500));
    setBattleStage('active');
  };

  const handleMove = async (moveName: string) => {
    if (isProcessing || gameOver || battleStage !== 'active') return;
    setIsProcessing(true);
    
    try {
      const result: TurnResult = await executeMove(moveName);
      
      for (const eventObj of (result.turn_info.battle_events as any[])) {
        const isPlayer = eventObj.is_player;
        
        if (eventObj.type === 'move') {
          setEvents(prev => [...prev, `${eventObj.attacker_name} used ${eventObj.move}!`]);
          
          if (isPlayer) {
            setPlayerAnim(prev => ({ ...prev, attacking: true }));
            setTimeout(() => setPlayerAnim(prev => ({ ...prev, attacking: false })), 300);
          } else {
            setOpponentAnim(prev => ({ ...prev, attacking: true }));
            setTimeout(() => setOpponentAnim(prev => ({ ...prev, attacking: false })), 300);
          }
          
          await new Promise(resolve => setTimeout(resolve, 400));
          
          if (eventObj.damage > 0) {
            hitSoundRef.current?.play();
            if (isPlayer) {
              setOpponentAnim(prev => ({ ...prev, shaking: true }));
              setTimeout(() => setOpponentAnim(prev => ({ ...prev, shaking: false })), 400);
            } else {
              setPlayerAnim(prev => ({ ...prev, shaking: true }));
              setTimeout(() => setPlayerAnim(prev => ({ ...prev, shaking: false })), 400);
            }
          }
        } else if (eventObj.type === 'effectiveness') {
          setEvents(prev => [...prev, eventObj.message]);
        } else if (eventObj.type === 'status') {
          setEvents(prev => [...prev, eventObj.message]);
        } else if (eventObj.type === 'faint') {
          setEvents(prev => [...prev, `${eventObj.pokemon_name} fainted!`]);
          if (eventObj.is_player) {
            setPlayerAnim(prev => ({ ...prev, fainted: true }));
          } else {
            setOpponentAnim(prev => ({ ...prev, fainted: true }));
          }
        } else if (eventObj.message) {
          setEvents(prev => [...prev, eventObj.message]);
        }

        if (eventObj.type === 'move') {
          setBattleState(prev => prev ? {
            ...prev,
            player_pokemon: {
              ...prev.player_pokemon,
              current_hp: isPlayer ? eventObj.attacker_hp : eventObj.defender_hp,
            },
            opponent_pokemon: {
              ...prev.opponent_pokemon,
              current_hp: isPlayer ? eventObj.defender_hp : eventObj.attacker_hp,
            }
          } : null);
        }
        
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      if (result.is_game_over) {
        setGameOver(result.battle_result);
        setBattleStage('gameover');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!battleState || !battleState.player_pokemon || !battleState.opponent_pokemon) {
    return <div className="min-h-screen bg-black flex items-center justify-center text-white font-retro text-xs animate-pulse">Initializing Battle Data...</div>;
  }

  return (
    <div className="min-h-screen bg-[#020617] text-white overflow-hidden relative font-retro flex flex-col">
      {showFlash && <div className="absolute inset-0 z-[100] animate-flash" />}

      {showStartOverlay && (
        <div className="absolute inset-0 z-[200] bg-black/95 flex flex-col items-center justify-center p-4">
          <div className="max-w-md w-full text-center space-y-8">
            <h2 className="text-2xl text-[#f8d030] uppercase tracking-[0.2em] animate-pulse" style={{ textShadow: '4px 4px 0 #000' }}>
              Battle Ready?
            </h2>
            <button 
              onClick={handleStartBattle}
              className="gba-box w-full py-6 text-xl hover:bg-[#2d3a4d] transition-colors uppercase tracking-widest text-white"
            >
              START BATTLE
            </button>
          </div>
        </div>
      )}

      {/* MAIN SHOWDOWN-STYLE LAYOUT */}
      <main className="flex-1 flex flex-col md:flex-row h-screen overflow-hidden p-2 md:p-4 gap-2 md:gap-4">
        
        {/* LEFT COLUMN: Visuals & Moves */}
        <div className="flex-[2] flex flex-col gap-2 md:gap-4 h-full">
          
          {/* BATTLE ARENA */}
          <div className="relative h-[300px] md:flex-1 bg-gray-950 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center border-2 md:border-4 border-[#475569] rounded-lg md:rounded-xl overflow-hidden gba-panel-shadow shrink-0">
            <div className="absolute inset-0 bg-black/40" />
            
            {/* Turn Counter Overlay */}
            <div className="absolute top-2 right-2 md:top-4 md:right-4 bg-black/60 px-2 md:px-3 py-1 border border-white/10 text-[8px] md:text-[10px] text-yellow-500 z-20">
              TURN {events.filter(e => e.includes('used')).length + 1}
            </div>

            {/* TOP SECTION: Opponent Status & Sprite */}
            <div className="absolute top-4 md:top-8 left-0 right-0 h-[40%] px-4 md:px-8">
              <div className="absolute top-0 left-4 md:left-8 scale-75 md:scale-100 origin-top-left">
                <PokemonCard
                  name={battleState.opponent_pokemon.name}
                  sprite={battleState.opponent_pokemon.sprite}
                  currentHp={battleState.opponent_pokemon.current_hp}
                  maxHp={battleState.opponent_pokemon.max_hp}
                  level={100}
                  types={battleState.opponent_pokemon.types}
                  isOpponent
                  showStatus={opponentAnim.status}
                  layout="status-only"
                />
              </div>
              <div className="absolute top-0 right-4 md:right-16 scale-75 md:scale-100 origin-top-right">
                <PokemonCard
                  name={battleState.opponent_pokemon.name}
                  sprite={battleState.opponent_pokemon.sprite}
                  currentHp={battleState.opponent_pokemon.current_hp}
                  maxHp={battleState.opponent_pokemon.max_hp}
                  level={100}
                  types={battleState.opponent_pokemon.types}
                  isOpponent
                  isVisible={opponentAnim.visible}
                  isShaking={opponentAnim.shaking}
                  isAttacking={opponentAnim.attacking}
                  isFainted={opponentAnim.fainted}
                  layout="sprite-only"
                />
              </div>
            </div>

            {/* MIDDLE SECTION: Player Sprite & Status */}
            <div className="absolute bottom-4 md:bottom-8 left-0 right-0 h-[40%] px-4 md:px-8">
              <div className="absolute bottom-0 left-4 md:left-16 scale-75 md:scale-100 origin-bottom-left">
                <PokemonCard
                  name={battleState.player_pokemon.name}
                  sprite={battleState.player_pokemon.sprite}
                  currentHp={battleState.player_pokemon.current_hp}
                  maxHp={battleState.player_pokemon.max_hp}
                  level={100}
                  types={battleState.player_pokemon.types}
                  isVisible={playerAnim.visible}
                  isShaking={playerAnim.shaking}
                  isAttacking={playerAnim.attacking}
                  isFainted={playerAnim.fainted}
                  layout="sprite-only"
                  flip={false}
                />
              </div>
              <div className="absolute bottom-0 right-4 md:right-8 scale-75 md:scale-100 origin-bottom-right">
                <PokemonCard
                  name={battleState.player_pokemon.name}
                  sprite={battleState.player_pokemon.sprite}
                  currentHp={battleState.player_pokemon.current_hp}
                  maxHp={battleState.player_pokemon.max_hp}
                  level={100}
                  types={battleState.player_pokemon.types}
                  showStatus={playerAnim.status}
                  layout="status-only"
                />
              </div>
            </div>
          </div>

          {/* MOVE SELECTION AREA */}
          <div className="h-40 md:h-48 gba-box flex flex-col justify-center relative gba-panel-shadow shrink-0">
            {gameOver ? (
              <div className="flex flex-col items-center justify-center h-full p-4">
                <p className="text-sm md:text-xl text-yellow-500 uppercase mb-2 md:mb-4 tracking-widest animate-pulse">{gameOver}</p>
                <button 
                  onClick={() => router.push('/')}
                  className="px-6 md:px-12 py-2 md:py-3 bg-red-900/40 border-2 md:border-4 border-red-800 text-white text-[10px] md:text-xs uppercase hover:bg-red-800 transition-colors"
                >
                  RETURN TO HOME
                </button>
              </div>
            ) : (
              <div className="flex h-full">
                {/* Left: Move Grid */}
                <div className="w-[60%] md:w-[70%] grid grid-cols-2 gap-x-1 md:gap-x-2 gap-y-2 md:gap-y-4 p-3 md:p-6 items-center border-r-2 md:border-r-4 border-[#0f172a]">
                  {battleState.player_moves.map(move => (
                    <button
                      key={move.name}
                      onClick={() => handleMove(move.name)}
                      onMouseEnter={() => setHoveredMove(move)}
                      onMouseLeave={() => setHoveredMove(null)}
                      onTouchStart={() => setHoveredMove(move)}
                      disabled={isProcessing || move.pp <= 0 || battleStage !== 'active'}
                      className={`text-left text-[9px] md:text-[12px] uppercase group flex items-center gap-1 md:gap-3
                        ${isProcessing || battleStage !== 'active' ? 'opacity-50' : 'hover:text-red-400'}
                      `}
                    >
                      <span className="opacity-0 group-hover:opacity-100 w-0 h-0 border-l-[4px] md:border-l-[8px] border-l-red-500 border-t-[3px] md:border-t-[6px] border-t-transparent border-b-[3px] md:border-b-[6px] border-b-transparent" />
                      {move.name.replace('-', ' ')}
                    </button>
                  ))}
                </div>

                {/* Right: Info & Run */}
                <div className="w-[40%] md:w-[30%] flex flex-col bg-black/20">
                  <div className="flex-1 p-2 md:p-4 flex flex-col justify-center gap-2 md:gap-4">
                    <div className="flex flex-col">
                      <span className="text-gray-500 text-[6px] md:text-[8px] uppercase mb-0.5 md:mb-1">Move Detail</span>
                      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-1">
                        <span className="text-white text-[9px] md:text-[12px]">{hoveredMove ? `${hoveredMove.pp}/${hoveredMove.max_pp} PP` : '--/--'}</span>
                        <span className={`text-[7px] md:text-[9px] px-1 md:px-2 py-0.5 rounded-sm inline-block text-center ${hoveredMove ? `type-${hoveredMove.type.toLowerCase()}` : 'bg-gray-800 text-gray-600'}`}>
                          {hoveredMove ? hoveredMove.type : '--'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => confirm('Forfeit?') && router.push('/')}
                    className="h-8 md:h-12 border-t-2 md:border-t-4 border-[#0f172a] text-[8px] md:text-[10px] uppercase text-gray-500 hover:text-white transition-colors flex items-center justify-center gap-1 md:gap-2 group"
                  >
                    <span className="opacity-0 group-hover:opacity-100 w-0 h-0 border-l-[4px] md:border-l-[6px] border-l-white border-t-[3px] md:border-t-[4px] border-t-transparent border-b-[3px] md:border-b-[4px] border-b-transparent" />
                    RUN
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Battle Log */}
        <div className="flex-1 h-[200px] md:h-full min-w-full md:min-w-[320px] flex flex-col gap-1 md:gap-2">
          <div className="px-2 text-gray-500 text-[8px] md:text-[10px] uppercase tracking-widest flex justify-between">
            <span>Battle Log</span>
            <span className="animate-pulse text-green-500">LIVE</span>
          </div>
          <div className="flex-1 overflow-hidden">
            <BattleLog events={events} />
          </div>
        </div>

      </main>
    </div>
  );
}
