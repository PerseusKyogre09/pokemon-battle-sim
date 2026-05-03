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
    const response = await fetch(`http://localhost:5000/api/audio/signed-url/${filename}`);
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
    <div className="min-h-screen bg-gray-950 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      
      {showFlash && <div className="absolute inset-0 z-[100] animate-flash" />}

      {showStartOverlay && (
        <div className="absolute inset-0 z-[200] bg-black/90 flex flex-col items-center justify-center p-4">
          <div className="max-w-md w-full text-center space-y-8 animate-in fade-in zoom-in-95 duration-500">
            <div className="space-y-4">
              <div className="w-20 h-20 bg-yellow-500 mx-auto rounded-xl flex items-center justify-center shadow-[0_0_30px_rgba(234,179,8,0.4)] mb-8">
                <span className="text-gray-900 text-4xl font-black">!</span>
              </div>
              <h2 className="text-2xl font-retro text-yellow-500 uppercase tracking-[0.3em] mb-4">Battle Ready?</h2>
              <p className="text-gray-400 font-retro text-[10px] uppercase leading-relaxed opacity-70">
                Prepare for battle against {battleState?.opponent_pokemon.name}
              </p>
            </div>
            
            <button 
              onClick={handleStartBattle}
              className="group relative w-full py-8 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-retro text-xs border-4 border-yellow-600 transition-all shadow-[0_0_50px_rgba(234,179,8,0.2)] hover:shadow-[0_0_70px_rgba(234,179,8,0.4)] active:scale-95 overflow-hidden"
              style={{ clipPath: 'polygon(25px 0, 100% 0, 100% calc(100% - 25px), calc(100% - 25px) 100%, 0 100%, 0 25px)' }}
            >
              <span className="relative z-10">COMMENCE BATTLE</span>
              <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
            </button>
          </div>
        </div>
      )}

      <main className="container mx-auto h-screen flex flex-col justify-between relative z-10 py-12 px-4 md:px-20">
        
        {/* TOP ROW: Status (Left) & Opponent Sprite (Right) */}
        <div className="flex justify-between items-start w-full">
          <div className="mt-8">
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
          <div className="relative">
            <Pokeball type="opponent" visible={pokeballState.opponent} />
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
              flip={false}
            />
          </div>
        </div>

        {/* BOTTOM ROW: Player Sprite (Left) & Status (Right) */}
        <div className="flex justify-between items-end w-full">
          <div className="relative mb-8">
            <Pokeball type="player" visible={pokeballState.player} />
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
          <div className="mb-20">
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

        {/* UI Overlay */}
        <div className="w-full max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
          <div className="md:col-span-2">
            <BattleLog events={events} />
          </div>

          <div className="bg-gray-900/90 backdrop-blur-md border-4 border-gray-800 p-6 flex flex-col gap-4 shadow-2xl relative"
               style={{ clipPath: 'polygon(15px 0, 100% 0, 100% 100%, 0 100%, 0 15px)' }}>
            {gameOver ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <h2 className="text-sm font-retro text-yellow-500 uppercase tracking-widest animate-pulse text-center leading-relaxed">{gameOver}</h2>
                <button 
                  onClick={() => router.push('/')}
                  className="w-full py-4 bg-white/10 hover:bg-white/20 border-2 border-white/20 transition-all font-retro text-[10px] uppercase"
                >
                  NEW BATTLE
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3">
                  {battleState.player_moves.map(move => (
                    <button
                      key={move.name}
                      onClick={() => handleMove(move.name)}
                      disabled={isProcessing || move.pp <= 0 || battleStage !== 'active'}
                      className={`p-3 border-4 text-[9px] font-retro uppercase transition-all flex flex-col items-start gap-2 relative overflow-hidden group
                        ${isProcessing || battleStage !== 'active' ? 'opacity-50 cursor-not-allowed' : 'hover:scale-[1.02] active:scale-95'}
                        ${move.pp <= 0 ? 'bg-red-900/20 border-red-900/40 text-red-500' : 'bg-gray-800/50 border-gray-700 hover:border-blue-500/50'}
                      `}
                      style={{ clipPath: 'polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)' }}
                    >
                      <span className="truncate w-full text-left">{move.name.replace('-', ' ')}</span>
                      <div className="flex justify-between w-full items-center">
                        <span className={`text-[7px] px-1 py-0.5 rounded-sm type-${move.type.toLowerCase()}`}>{move.type}</span>
                        <span className="text-[7px] opacity-50">{move.pp}/{move.max_pp}</span>
                      </div>
                    </button>
                  ))}
                </div>
                <button 
                  onClick={() => {
                    if (confirm('Forfeit battle?')) router.push('/');
                  }}
                  className="mt-4 text-[8px] font-retro text-gray-500 hover:text-red-400 transition-colors uppercase tracking-widest text-center w-full"
                >
                  [ Forfeit ]
                </button>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
