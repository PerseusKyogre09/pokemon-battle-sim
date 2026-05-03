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
      // Robust cleanup to stop all audio on leave
      [audioRef, hitSoundRef, pokeballSoundRef].forEach(ref => {
        if (ref.current) {
          ref.current.pause();
          ref.current.currentTime = 0;
          ref.current = null;
        }
      });
    };
  }, [router]);

  const setupAudio = async () => {
    try {
      const [battleMusicUrl, hitSoundUrl, pokeballSoundUrl] = await Promise.all([
        getAudioUrl('battle-music.mp3'),
        getAudioUrl('hit-sound.mp3'),
        getAudioUrl('pokeball-throw.mp3')
      ]);

      audioRef.current = new Audio(battleMusicUrl);
      audioRef.current.loop = true;
      audioRef.current.volume = 0.3;
      audioRef.current.preload = 'auto';
      
      hitSoundRef.current = new Audio(hitSoundUrl);
      hitSoundRef.current.preload = 'auto';
      
      pokeballSoundRef.current = new Audio(pokeballSoundUrl);
      pokeballSoundRef.current.preload = 'auto';
    } catch (err) {
      console.error('Audio setup failed:', err);
    }
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

  const handleQuit = () => {
    // Explicitly stop all audio before navigating
    [audioRef, hitSoundRef, pokeballSoundRef].forEach(ref => {
      if (ref.current) {
        ref.current.pause();
        ref.current.currentTime = 0;
        ref.current = null;
      }
    });
    router.push('/');
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

      {/* MAIN LAYOUT: Vertical on mobile, Centered & Scaling on desktop */}
      <main className="flex-1 flex flex-col md:flex-row md:container md:mx-auto md:max-w-6xl 2xl:max-w-[1600px] h-screen md:overflow-hidden p-2 md:p-6 2xl:p-12 gap-4 md:gap-8 overflow-y-auto">
        
        {/* LEFT COLUMN: Visuals & Moves */}
        <div className="flex-[3] flex flex-col gap-4 2xl:gap-8 h-auto md:h-full">
          
          {/* BATTLE ARENA */}
          <div className="relative h-[300px] md:flex-[4] md:min-h-[450px] 2xl:min-h-[650px] bg-gray-950 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center border-4 2xl:border-8 border-[#475569] rounded-xl 2xl:rounded-3xl overflow-hidden gba-panel-shadow shrink-0 transition-all duration-700">
            <div className="absolute inset-0 bg-black/10" />
            
            {/* Pokeball Animations */}
            <Pokeball type="player" visible={pokeballState.player} />
            <Pokeball type="opponent" visible={pokeballState.opponent} />
            
            {/* Turn Counter Overlay */}
            <div className="absolute top-4 right-4 bg-black/60 px-3 py-1 border-2 border-white/10 text-[10px] 2xl:text-[14px] text-yellow-500 z-20 rounded-md">
              TURN {events.filter(e => e.includes('used')).length + 1}
            </div>

            {/* OPPONENT SECTION */}
            <div className="absolute top-4 left-4 md:top-8 md:left-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-top-left transition-all duration-500">
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
            <div className="absolute top-2 right-4 md:top-8 md:right-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-top-right transition-all duration-500">
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

            {/* PLAYER SECTION */}
            <div className="absolute bottom-2 left-4 md:bottom-8 md:left-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-bottom-left transition-all duration-500">
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
            <div className="absolute bottom-4 right-4 md:bottom-8 md:right-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-bottom-right transition-all duration-500">
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

          {/* MOVE SELECTION AREA */}
          <div className="h-48 md:h-[220px] 2xl:h-[300px] gba-box flex flex-col justify-center relative gba-panel-shadow shrink-0">
            {gameOver ? (
              <div className="flex flex-col items-center justify-center h-full p-6 bg-black/60 text-center">
                <p className="text-[10px] md:text-3xl text-yellow-500 uppercase mb-4 md:mb-8 tracking-[0.2em] md:tracking-[0.3em] animate-pulse font-bold leading-relaxed md:leading-normal max-w-[90%]">
                  {gameOver}
                </p>
                <button 
                  onClick={handleQuit}
                  className="px-8 md:px-20 py-2 md:py-5 bg-red-900/40 border-2 md:border-4 border-red-800 text-white text-[8px] md:text-sm uppercase hover:bg-red-800 transition-all tracking-[0.2em] md:tracking-[0.3em] font-bold"
                >
                  RETURN HOME
                </button>
              </div>
            ) : (
              <div className="flex h-full">
                {/* Left: Move Grid */}
                <div className="w-[60%] md:w-[70%] grid grid-cols-2 gap-x-2 md:gap-x-8 gap-y-4 md:gap-y-8 p-4 md:p-10 items-center border-r-4 border-[#0f172a]">
                  {battleState.player_moves.map(move => (
                    <button
                      key={move.name}
                      onClick={() => handleMove(move.name)}
                      onMouseEnter={() => setHoveredMove(move)}
                      onMouseLeave={() => setHoveredMove(null)}
                      onTouchStart={() => setHoveredMove(move)}
                      disabled={isProcessing || move.pp <= 0 || battleStage !== 'active'}
                      className={`text-left text-[11px] md:text-[18px] 2xl:text-[24px] uppercase group flex items-center gap-2 md:gap-6 transition-all
                        ${isProcessing || battleStage !== 'active' ? 'opacity-50' : 'hover:text-red-400 md:hover:translate-x-4'}
                      `}
                    >
                      <span className="hidden md:block opacity-0 group-hover:opacity-100 w-0 h-0 border-l-[12px] border-l-red-500 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent" />
                      {move.name.replace('-', ' ')}
                    </button>
                  ))}
                </div>

                {/* Right: Info & Run */}
                <div className="w-[40%] md:w-[30%] flex flex-col bg-black/20 md:bg-black/40">
                  <div className="flex-1 p-4 md:p-8 flex flex-col justify-center gap-4 md:gap-8">
                    <div className="flex flex-col">
                      <span className="text-gray-500 text-[8px] md:text-[12px] 2xl:text-[16px] uppercase mb-1 md:mb-3 tracking-[0.2em]">Move Detail</span>
                      <div className="flex flex-col gap-2 md:gap-4">
                        <span className="text-white text-[12px] md:text-[20px] 2xl:text-[28px] tracking-widest font-bold whitespace-nowrap">{hoveredMove ? `${hoveredMove.pp}/${hoveredMove.max_pp} PP` : '--/--'}</span>
                        <span className={`text-[8px] md:text-[10px] 2xl:text-[18px] px-2 md:px-5 py-1 md:py-2 rounded-md inline-block text-center tracking-[0.3em] font-bold uppercase ${hoveredMove ? `type-${hoveredMove.type.toLowerCase()}` : 'bg-gray-800 text-gray-600'}`}>
                          {hoveredMove ? hoveredMove.type : 'NONE'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => confirm('Forfeit?') && handleQuit()}
                    className="h-12 md:h-20 border-t-4 border-[#0f172a] text-[10px] md:text-[14px] 2xl:text-[18px] uppercase text-gray-500 hover:text-white transition-all flex items-center justify-center gap-2 group hover:bg-white/5 tracking-[0.2em]"
                  >
                    <span className="opacity-0 group-hover:opacity-100 w-0 h-0 border-l-[10px] border-l-white border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent" />
                    RUN
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Battle Log */}
        <div className="h-[250px] md:flex-1 md:h-full md:min-w-[400px] 2xl:min-w-[500px] flex flex-col gap-2 md:gap-6 shrink-0 pb-8 md:pb-0">
          <div className="px-2 text-gray-500 text-[10px] md:text-[12px] 2xl:text-[16px] uppercase tracking-[0.3em] flex justify-between items-center">
            <span>Battle Log</span>
            <span className="animate-pulse text-green-500 text-[8px] md:text-[10px] 2xl:text-[14px] flex items-center gap-2">
              <span className="w-1.5 h-1.5 md:w-2 md:h-2 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]" /> LIVE
            </span>
          </div>
          <div className="flex-1 overflow-hidden gba-panel-shadow rounded-xl 2xl:rounded-3xl border-4 2xl:border-8 border-[#475569]">
            <BattleLog events={events} />
          </div>
        </div>

      </main>
    </div>
  );
}
