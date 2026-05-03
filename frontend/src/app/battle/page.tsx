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
    <div className="min-h-screen bg-gray-950 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center text-white overflow-hidden relative font-retro">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      
      {showFlash && <div className="absolute inset-0 z-[100] animate-flash" />}

      {showStartOverlay && (
        <div className="absolute inset-0 z-[200] bg-black/95 flex flex-col items-center justify-center p-4">
          <div className="max-w-md w-full text-center space-y-8">
            <h2 className="text-2xl text-[#f8d030] uppercase tracking-[0.2em] animate-pulse" style={{ textShadow: '4px 4px 0 #404040' }}>
              Battle Ready?
            </h2>
            <button 
              onClick={handleStartBattle}
              className="gba-box w-full py-6 text-xl hover:bg-[#ffffeb] transition-colors uppercase tracking-widest"
            >
              START BATTLE
            </button>
          </div>
        </div>
      )}

      <main className="container mx-auto h-screen flex flex-col relative z-10 max-w-4xl pt-8">
        
        {/* TOP SECTION: Opponent Status (Left) & Sprite (Right) */}
        <div className="relative h-[40%] w-full">
          {/* Opponent Status Box - Top Left */}
          <div className="absolute top-4 left-0">
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
          
          {/* Opponent Sprite - Top Right */}
          <div className="absolute top-0 right-10">
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

        {/* MIDDLE SECTION: Player Sprite (Left) & Status (Right) */}
        <div className="relative h-[40%] w-full">
          {/* Player Sprite - Bottom Left */}
          <div className="absolute bottom-0 left-10">
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

          {/* Player Status Box - Bottom Right */}
          <div className="absolute bottom-4 right-0">
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

        {/* BOTTOM SECTION: GBA Control Panel */}
        <div className="h-[20%] w-full grid grid-cols-1 md:grid-cols-5 gap-0 mt-auto border-t-4 border-black">
          {/* Text/Log Area */}
          <div className="md:col-span-3 h-full">
            <BattleLog events={events} />
          </div>

            {/* Move Selection Area */}
            <div className="md:col-span-2 h-full gba-box rounded-none border-l-0 flex flex-col justify-center relative">
              {gameOver ? (
                <div className="flex flex-col items-center justify-center h-full p-2">
                  <p className="text-[10px] text-gray-700 uppercase mb-2">{gameOver}</p>
                  <button 
                    onClick={() => router.push('/')}
                    className="w-full py-2 bg-gray-700 border-2 border-gray-600 text-[10px] uppercase text-white hover:bg-gray-600"
                  >
                    RETRY
                  </button>
                </div>
              ) : (
                <div className="flex h-full">
                  {/* Left: Move Grid */}
                  <div className="w-[65%] grid grid-cols-2 gap-x-1 gap-y-4 p-3 items-center border-r-2 border-white/5">
                    {battleState.player_moves.map(move => (
                      <button
                        key={move.name}
                        onClick={() => handleMove(move.name)}
                        onMouseEnter={() => setHoveredMove(move)}
                        onMouseLeave={() => setHoveredMove(null)}
                        disabled={isProcessing || move.pp <= 0 || battleStage !== 'active'}
                        className={`text-left text-[10px] uppercase group flex items-center gap-1
                          ${isProcessing || battleStage !== 'active' ? 'opacity-50' : 'hover:text-red-400'}
                        `}
                      >
                        <span className="opacity-0 group-hover:opacity-100 w-0 h-0 border-l-[6px] border-l-red-500 border-t-[5px] border-t-transparent border-b-[5px] border-b-transparent" />
                        {move.name.replace('-', ' ')}
                      </button>
                    ))}
                  </div>

                  {/* Right: Info & Forfeit */}
                  <div className="w-[35%] flex flex-col">
                    {/* PP/Type Info (Fixed, not overlay) */}
                    <div className="flex-1 p-3 flex flex-col justify-center gap-3 border-b-2 border-white/5">
                      <div className="flex flex-col">
                        <span className="text-gray-500 text-[7px] uppercase mb-1">PP</span>
                        <span className="text-white text-[10px]">{hoveredMove ? `${hoveredMove.pp}/${hoveredMove.max_pp}` : '--/--'}</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-gray-500 text-[7px] uppercase mb-1">TYPE</span>
                        <span className={`text-[8px] px-1 py-0.5 rounded-sm text-center ${hoveredMove ? `type-${hoveredMove.type.toLowerCase()}` : 'bg-gray-800 text-gray-600'}`}>
                          {hoveredMove ? hoveredMove.type : '--'}
                        </span>
                      </div>
                    </div>
                    
                    {/* Forfeit button */}
                    <div className="h-[30%] flex items-center justify-center p-2">
                      <button 
                        onClick={() => confirm('Forfeit?') && router.push('/')}
                        className="text-[8px] uppercase text-gray-500 hover:text-white transition-colors group flex items-center gap-1"
                      >
                        <span className="opacity-0 group-hover:opacity-100 w-0 h-0 border-l-[4px] border-l-white border-t-[3px] border-t-transparent border-b-[3px] border-b-transparent" />
                        RUN
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
        </div>
      </main>
    </div>
  );
}
