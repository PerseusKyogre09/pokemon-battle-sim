'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { API_BASE_URL, BattleState, executeMove, TurnResult } from '@/lib/api';
import PokemonCard from '@/components/PokemonCard';
import BattleLog from '@/components/BattleLog';
import Pokeball from '@/components/Pokeball';
import WeatherOverlay from '@/components/WeatherOverlay';
import { resolveMoveAnimation, TYPE_COLORS, MoveTemplates, ActionAtoms } from '@/lib/animations/MoveAnimations';
import { gsap } from 'gsap';

type BattleStage = 'intro-opponent' | 'intro-player' | 'active' | 'gameover';

const getAudioUrl = async (filename: string) => {
  try {
    const baseUrl = API_BASE_URL.endsWith('/api') ? API_BASE_URL.replace(/\/api$/, '') : API_BASE_URL;
    const response = await fetch(`${baseUrl}/api/audio/signed-url/${filename}`);
    const data = await response.json();
    return data.url;
  } catch (error) {
    console.error(`Error fetching audio: ${filename}`, error);
    return `/music/${filename}`;
  }
};

export default function BattlePage() {
  const [battleState, setBattleState] = useState<BattleState | null>(null);
  const [events, setEvents] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [gameOver, setGameOver] = useState<string | null>(null);
  const [battleStage, setBattleStage] = useState<BattleStage>('intro-opponent');
  const [weather, setWeather] = useState('none');
  
  const [playerAnim, setPlayerAnim] = useState({ visible: false, status: false, attacking: false, shaking: false, fainted: false });
  const [opponentAnim, setOpponentAnim] = useState({ visible: false, status: false, attacking: false, shaking: false, fainted: false });
  const [pokeballState, setPokeballState] = useState({ player: false, opponent: false });
  const [showFlash, setShowFlash] = useState(false);
  const [showStartOverlay, setShowStartOverlay] = useState(true);
  const [hoveredMove, setHoveredMove] = useState<any>(null);
  const [abilityPopup, setAbilityPopup] = useState<{ name: string, pokemon: string, isPlayer: boolean, exiting?: boolean } | null>(null);
  const [audioReady, setAudioReady] = useState(false);
  const [showForfeitModal, setShowForfeitModal] = useState(false);
  const [showSwitchMenu, setShowSwitchMenu] = useState(false);

  const router = useRouter();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const hitSoundRef = useRef<HTMLAudioElement | null>(null);
  const pokeballSoundRef = useRef<HTMLAudioElement | null>(null);
  const abilityPopupTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const playerSpriteRef = useRef<HTMLDivElement>(null);
  const opponentSpriteRef = useRef<HTMLDivElement>(null);
  const arenaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const savedState = localStorage.getItem('initialBattleState');
    if (savedState && savedState !== 'undefined') {
      try {
        const state = JSON.parse(savedState);
        setBattleState(state);
        setupAudio();
      } catch (e) {
        localStorage.removeItem('initialBattleState');
        router.push('/');
      }
    } else {
      router.push('/');
    }

    return () => {
      [audioRef, hitSoundRef, pokeballSoundRef].forEach(ref => {
        if (ref.current) {
          ref.current.pause();
          ref.current.currentTime = 0;
          ref.current = null;
        }
      });
      if ((window as any).__activeAudios) {
        (window as any).__activeAudios.forEach((a: HTMLAudioElement) => {
          try { a.pause(); a.currentTime = 0; } catch (e) {}
        });
        (window as any).__activeAudios = [];
      }
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
      
      (window as any).__activeAudios = [audioRef.current, hitSoundRef.current, pokeballSoundRef.current];
      setAudioReady(true);
    } catch (err) {
      setAudioReady(true);
    }
  };

  const playDynamicAudio = (url: string) => {
    try {
      const audio = new Audio(url);
      if (!(window as any).__activeAudios) (window as any).__activeAudios = [];
      (window as any).__activeAudios.push(audio);
      audio.play().catch(() => {});
    } catch (e) {}
  };

  const showAbilityPopup = (popup: { name: string; pokemon: string; isPlayer: boolean }) => {
    if (abilityPopupTimerRef.current) clearTimeout(abilityPopupTimerRef.current);
    setAbilityPopup(popup);
    abilityPopupTimerRef.current = setTimeout(() => {
      setAbilityPopup(prev => prev ? { ...prev, exiting: true } : null);
      abilityPopupTimerRef.current = setTimeout(() => {
        setAbilityPopup(null);
        abilityPopupTimerRef.current = null;
      }, 500);
    }, 2400);
  };

  const handleStartBattle = () => {
    if (!battleState) return;
    setShowStartOverlay(false);
    startIntroSequence(battleState);
  };

  const startIntroSequence = async (state: BattleState) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    audioRef.current?.play().catch(() => {});
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setPokeballState({ player: false, opponent: true });
    pokeballSoundRef.current?.play().catch(() => {});
    setEvents([`A wild ${state.opponent_pokemon.name} appeared!`]);
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setPokeballState({ player: false, opponent: false });
    setShowFlash(true);
    setTimeout(() => setShowFlash(false), 300);
    setOpponentAnim(prev => ({ ...prev, visible: true }));
    if (state.opponent_pokemon.cry_url) playDynamicAudio(state.opponent_pokemon.cry_url);
    
    await new Promise(resolve => setTimeout(resolve, 800));
    setOpponentAnim(prev => ({ ...prev, status: true }));
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setBattleStage('intro-player');
    setPokeballState({ player: true, opponent: false });
    pokeballSoundRef.current?.play().catch(() => {});
    setEvents(prev => [...prev, `Go! ${state.player_pokemon.name}!`]);
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setPokeballState({ player: false, opponent: false });
    setShowFlash(true);
    setTimeout(() => setShowFlash(false), 300);
    setPlayerAnim(prev => ({ ...prev, visible: true }));
    if (state.player_pokemon.cry_url) playDynamicAudio(state.player_pokemon.cry_url);
    
    await new Promise(resolve => setTimeout(resolve, 800));
    setPlayerAnim(prev => ({ ...prev, status: true }));
    await new Promise(resolve => setTimeout(resolve, 500));

    if (state.start_events) {
      for (const event of state.start_events) {
        if (event.type === 'ability') {
          showAbilityPopup({ name: event.ability_name, pokemon: event.pokemon_name, isPlayer: event.is_player });
          await new Promise(resolve => setTimeout(resolve, 600));
          if (event.set_weather) setWeather(event.set_weather);
          setEvents(prev => [...prev, event.message]);
          await new Promise(resolve => setTimeout(resolve, 1800));
        }
      }
    }
    setBattleStage('active');
  };

  const handleQuit = () => {
    [audioRef, hitSoundRef, pokeballSoundRef].forEach(ref => {
      if (ref.current) {
        ref.current.pause();
        ref.current.currentTime = 0;
        ref.current = null;
      }
    });
    router.push('/');
  };

  const handleMove = async (moveName?: string, switchIndex?: number) => {
    if (isProcessing || gameOver || battleStage !== 'active') return;
    setIsProcessing(true);
    
    try {
      const result: TurnResult | any = moveName ? await executeMove(moveName) : await executeMove(undefined, switchIndex);
      if (!result || !result.turn_info) {
        setIsProcessing(false);
        return;
      }
      setShowSwitchMenu(false);

      for (const eventObj of (result.turn_info.battle_events as any[])) {
        if (eventObj.type === 'move') {
          setEvents(prev => [...prev, `${eventObj.attacker_name} used ${eventObj.move}!`]);
          const isAttackerPlayer = eventObj.attacker_name === battleState?.player_pokemon.name;
          const attackerEl = isAttackerPlayer ? playerSpriteRef.current : opponentSpriteRef.current;
          const defenderEl = isAttackerPlayer ? opponentSpriteRef.current : playerSpriteRef.current;

          const isMiss = eventObj.status_message?.toLowerCase().includes('missed');

          if (attackerEl && defenderEl && !isMiss) {
            const anim = resolveMoveAnimation(eventObj.move, '', eventObj.category || 'physical', arenaRef.current || undefined);
            await anim(attackerEl, defenderEl, isAttackerPlayer);
          } else {
            // If it missed or targets are missing, just show a quick attack bounce
            if (isAttackerPlayer) {
              setPlayerAnim(prev => ({ ...prev, attacking: true }));
              setTimeout(() => setPlayerAnim(prev => ({ ...prev, attacking: false })), 200);
            } else {
              setOpponentAnim(prev => ({ ...prev, attacking: true }));
              setTimeout(() => setOpponentAnim(prev => ({ ...prev, attacking: false })), 200);
            }
            await new Promise(resolve => setTimeout(resolve, 300));
          }
          if (eventObj.damage > 0 || eventObj.substitute_damage > 0) hitSoundRef.current?.play();
          if (eventObj.status_message) setEvents(prev => [...prev, eventObj.status_message]);
        } else if (eventObj.type === 'recall') {
          if (eventObj.message) setEvents(prev => [...prev, eventObj.message]);
          if (eventObj.is_player_switch) setPlayerAnim(prev => ({ ...prev, visible: false }));
          else if (eventObj.is_opponent_switch) setOpponentAnim(prev => ({ ...prev, visible: false }));
          await new Promise(resolve => setTimeout(resolve, 700));
        } else if (eventObj.type === 'status') {
          if (eventObj.message) {
            setEvents(prev => [...prev, eventObj.message]);
            const lowerMsg = eventObj.message.toLowerCase();
            const targetEl = eventObj.target === 'player' ? playerSpriteRef.current : opponentSpriteRef.current;
            if (targetEl) {
              if (lowerMsg.includes('hurt by its burn')) await MoveTemplates.statusDamage(targetEl, 'Burn');
              else if (lowerMsg.includes('hurt by poison')) await MoveTemplates.statusDamage(targetEl, 'Poison');
            }
          }
          if (eventObj.is_player_switch) {
            setPlayerAnim(prev => ({ ...prev, visible: false }));
            await new Promise(resolve => setTimeout(resolve, 300));
            setPokeballState({ player: true, opponent: false });
            pokeballSoundRef.current?.play().catch(() => {});
            await new Promise(resolve => setTimeout(resolve, 600));
            if (eventObj.new_pokemon_name && result.player_team) {
              const newMon = result.player_team.find((p: any) => p.name === eventObj.new_pokemon_name);
              if (newMon) {
                setBattleState(prev => prev ? { ...prev, player_pokemon: { ...newMon, current_hp: eventObj.player_hp ?? newMon.current_hp } } : null);
                if (newMon.cry_url) playDynamicAudio(newMon.cry_url);
              }
            }
            setPokeballState({ player: false, opponent: false });
            setShowFlash(true);
            setTimeout(() => setShowFlash(false), 200);
            setPlayerAnim(prev => ({ ...prev, visible: true, fainted: false }));
            if (playerSpriteRef.current) gsap.set(playerSpriteRef.current, { y: 0, opacity: 1, scale: 1 });
            await new Promise(resolve => setTimeout(resolve, 400));
          } else if (eventObj.is_opponent_switch) {
            setOpponentAnim(prev => ({ ...prev, visible: false }));
            await new Promise(resolve => setTimeout(resolve, 300));
            setPokeballState({ player: false, opponent: true });
            pokeballSoundRef.current?.play().catch(() => {});
            await new Promise(resolve => setTimeout(resolve, 600));
            if (eventObj.new_pokemon_name && result.opponent_team) {
              const newMon = result.opponent_team.find((p: any) => p.name === eventObj.new_pokemon_name);
              if (newMon) {
                setBattleState(prev => prev ? { ...prev, opponent_pokemon: { ...newMon, current_hp: eventObj.opponent_hp ?? newMon.current_hp } } : null);
                if (newMon.cry_url) playDynamicAudio(newMon.cry_url);
              }
            }
            setPokeballState({ player: false, opponent: false });
            setShowFlash(true);
            setTimeout(() => setShowFlash(false), 200);
            setOpponentAnim(prev => ({ ...prev, visible: true, fainted: false }));
            if (opponentSpriteRef.current) gsap.set(opponentSpriteRef.current, { y: 0, opacity: 1, scale: 1 });
            await new Promise(resolve => setTimeout(resolve, 400));
          }
        } else if (eventObj.type === 'effectiveness') {
          setEvents(prev => [...prev, eventObj.message]);
        } else if (eventObj.type === 'faint') {
          setEvents(prev => [...prev, `${eventObj.pokemon_name} fainted!`]);
          const targetEl = eventObj.is_player ? playerSpriteRef.current : opponentSpriteRef.current;
          if (targetEl) await ActionAtoms.faint(targetEl);
          else {
            if (eventObj.is_player) setPlayerAnim(prev => ({ ...prev, fainted: true }));
            else setOpponentAnim(prev => ({ ...prev, fainted: true }));
            await new Promise(resolve => setTimeout(resolve, 800));
          }
        } else if (eventObj.type === 'ability') {
          showAbilityPopup({ name: eventObj.ability_name, pokemon: eventObj.pokemon_name, isPlayer: eventObj.is_player === true });
          
          // Handle mid-animation form changes (e.g. Stance Change, Hunger Switch)
          if (eventObj.new_sprite || eventObj.new_name) {
            const side = eventObj.target === 'player' ? 'player_pokemon' : 'opponent_pokemon';
            setBattleState(prev => {
              if (!prev) return prev;
              return {
                ...prev,
                [side]: {
                  ...prev[side],
                  ...(eventObj.new_sprite ? { sprite: eventObj.new_sprite } : {}),
                  ...(eventObj.new_name ? { name: eventObj.new_name } : {})
                }
              };
            });
          }
          await new Promise(resolve => setTimeout(resolve, 600));
          setEvents(prev => [...prev, eventObj.message]);
          await new Promise(resolve => setTimeout(resolve, 1800));
        } else if (eventObj.type === 'pending_switch') {
          if (eventObj.message) setEvents(prev => [...prev, eventObj.message]);
          if (eventObj.target === 'player') {
            setTimeout(() => setShowSwitchMenu(true), 500);
          }
        } else if (eventObj.message) {
          setEvents(prev => [...prev, eventObj.message]);
        }

        if (eventObj.set_weather) setWeather(eventObj.set_weather);

        const isSwitchEvent = eventObj.is_player_switch || eventObj.is_opponent_switch || eventObj.type === 'recall';
        if (!isSwitchEvent && (eventObj.type === 'move' || eventObj.type === 'status' || eventObj.type === 'ability' || eventObj.type === 'item')) {
          if (eventObj.player_hp !== undefined && eventObj.opponent_hp !== undefined) {
             setBattleState(prev => prev ? {
               ...prev,
               player_pokemon: { ...prev.player_pokemon, current_hp: eventObj.player_hp },
               opponent_pokemon: { ...prev.opponent_pokemon, current_hp: eventObj.opponent_hp }
             } : null);
          }
        }
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      if (result.player_pokemon) {
        setBattleState(prev => ({ ...prev, ...result } as any));
        if (result.player_pokemon.current_hp > 0) setPlayerAnim(prev => ({ ...prev, fainted: false }));
        if (result.opponent_pokemon.current_hp > 0) setOpponentAnim(prev => ({ ...prev, fainted: false }));
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
            <h2 className="text-2xl text-[#f8d030] uppercase tracking-[0.2em] animate-pulse" style={{ textShadow: '4px 4px 0 #000' }}>Battle Ready?</h2>
            <button onClick={handleStartBattle} disabled={!audioReady} className={`gba-box w-full py-6 text-xl hover:bg-[#2d3a4d] transition-colors uppercase tracking-widest text-white ${!audioReady ? 'opacity-50 cursor-wait' : ''}`}>
              {audioReady ? 'START BATTLE' : 'LOADING AUDIO...'}
            </button>
          </div>
        </div>
      )}

      <main className="flex-1 flex flex-col md:flex-row md:container md:mx-auto md:max-w-6xl 2xl:max-w-[1600px] h-screen md:overflow-hidden p-2 md:p-6 2xl:p-12 gap-4 md:gap-8 overflow-y-auto">
        <div className="flex-[3] flex flex-col gap-4 2xl:gap-8 h-auto md:h-full">
          <div ref={arenaRef} className="relative h-[300px] md:flex-[4] md:min-h-[450px] 2xl:min-h-[650px] bg-gray-950 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center border-4 2xl:border-8 border-[#475569] rounded-xl 2xl:rounded-3xl overflow-hidden gba-panel-shadow shrink-0 transition-all duration-700">
            <div className="absolute inset-0 bg-black/10" />
            <WeatherOverlay weather={weather} />
            <Pokeball type="player" visible={pokeballState.player} />
            <Pokeball type="opponent" visible={pokeballState.opponent} />
            
            <div className="absolute top-4 right-4 bg-black/60 px-3 py-1 border-2 border-white/10 text-[10px] 2xl:text-[14px] text-yellow-500 z-20 rounded-md">
              TURN {events.filter(e => e && e.includes('used')).length + 1}
            </div>

            {abilityPopup && (
              <div key={`${abilityPopup.pokemon}-${abilityPopup.name}`} className={`absolute z-[100] ${abilityPopup.isPlayer ? 'bottom-[35%] left-0' : 'top-[28%] right-0'}`} style={{ willChange: 'transform, opacity' }}>
                <div className={`relative flex items-center ${abilityPopup.isPlayer ? (abilityPopup.exiting ? 'animate-ability-out-player' : 'animate-ability-in-player') : (abilityPopup.exiting ? 'animate-ability-out-opponent' : 'animate-ability-in-opponent')}`}>
                  <div className={`bg-black/90 border-y-2 border-white/20 px-6 py-2.5 flex items-center gap-5 min-w-[220px] shadow-[0_10px_25px_rgba(0,0,0,0.5)] ${abilityPopup.isPlayer ? 'rounded-r-full pl-12 pr-10' : 'rounded-l-full pr-12 pl-10'}`}>
                    <div className="bg-[#4a5568] text-white text-[7px] md:text-[9px] px-2 py-0.5 rounded-sm tracking-widest font-bold border border-white/10 shadow-sm">ABILITY</div>
                    <span className="text-white text-[12px] md:text-[17px] font-bold uppercase tracking-[0.2em]" style={{ textShadow: '2px 2px 2px rgba(0,0,0,0.8)' }}>{abilityPopup.name}</span>
                  </div>
                  <div className={`absolute top-0 bottom-0 w-1.5 bg-yellow-400 ${abilityPopup.isPlayer ? 'left-0' : 'right-0'}`} />
                </div>
              </div>
            )}

            {showForfeitModal && (
              <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 backdrop-blur-sm">
                <div className="bg-gradient-to-br from-slate-700/80 to-slate-900/90 border border-red-500/40 rounded-xl shadow-[0_20px_60px_rgba(220,38,38,0.3)] p-6 md:p-8 w-80 md:w-96 animate-in fade-in scale-95">
                  <div className="flex justify-center mb-5"><img src="/images/pokeball.png" alt="Pokeball" className="w-16 h-16 md:w-20 md:h-20 drop-shadow-lg" /></div>
                  <div className="text-center mb-6">
                    <h2 className="text-white text-xl md:text-2xl font-bold uppercase tracking-[0.2em] mb-2">Forfeit?</h2>
                    <p className="text-gray-300 text-xs md:text-sm leading-relaxed">Give up this battle?</p>
                  </div>
                  <div className="flex gap-3 md:gap-4">
                    <button onClick={() => setShowForfeitModal(false)} className="flex-1 px-4 py-2.5 md:py-3 bg-slate-600/60 hover:bg-slate-600 text-white font-semibold uppercase tracking-[0.15em] rounded-lg transition-all duration-200 text-xs md:text-sm border border-slate-500/40">Cancel</button>
                    <button onClick={() => { setShowForfeitModal(false); handleQuit(); }} className="flex-1 px-4 py-2.5 md:py-3 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-semibold uppercase tracking-[0.15em] rounded-lg transition-all duration-200 text-xs md:text-sm shadow-[0_4px_12px_rgba(220,38,38,0.35)]">Forfeit</button>
                  </div>
                </div>
              </div>
            )}

            <div className="absolute top-4 left-4 md:top-8 md:left-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-top-left transition-all duration-500">
              <PokemonCard name={battleState.opponent_pokemon.name} sprite={battleState.opponent_pokemon.sprite} currentHp={battleState.opponent_pokemon.current_hp} maxHp={battleState.opponent_pokemon.max_hp} level={100} types={battleState.opponent_pokemon.types} status_effects={battleState.opponent_pokemon.status_effects} isOpponent showStatus={opponentAnim.status} layout="status-only" hasSubstitute={(battleState.opponent_pokemon.substitute_hp ?? 0) > 0} />
            </div>
            <div className="absolute top-2 right-4 md:top-8 md:right-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-top-right transition-all duration-500">
              <PokemonCard ref={opponentSpriteRef} name={battleState.opponent_pokemon.name} sprite={battleState.opponent_pokemon.sprite} currentHp={battleState.opponent_pokemon.current_hp} maxHp={battleState.opponent_pokemon.max_hp} level={100} types={battleState.opponent_pokemon.types} status_effects={battleState.opponent_pokemon.status_effects} isOpponent isVisible={opponentAnim.visible} isShaking={opponentAnim.shaking} isAttacking={opponentAnim.attacking} isFainted={opponentAnim.fainted} layout="sprite-only" hasSubstitute={(battleState.opponent_pokemon.substitute_hp ?? 0) > 0} />
            </div>

            <div className="absolute bottom-2 left-4 md:bottom-8 md:left-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-bottom-left transition-all duration-500">
              <PokemonCard ref={playerSpriteRef} name={battleState.player_pokemon.name} sprite={battleState.player_pokemon.sprite} currentHp={battleState.player_pokemon.current_hp} maxHp={battleState.player_pokemon.max_hp} level={100} types={battleState.player_pokemon.types} status_effects={battleState.player_pokemon.status_effects} isVisible={playerAnim.visible} isShaking={playerAnim.shaking} isAttacking={playerAnim.attacking} isFainted={playerAnim.fainted} layout="sprite-only" flip={false} hasSubstitute={(battleState.player_pokemon.substitute_hp ?? 0) > 0} />
            </div>
            <div className="absolute bottom-4 right-4 md:bottom-8 md:right-8 scale-75 md:scale-100 2xl:scale-[1.4] origin-bottom-right transition-all duration-500">
              <PokemonCard name={battleState.player_pokemon.name} sprite={battleState.player_pokemon.sprite} currentHp={battleState.player_pokemon.current_hp} maxHp={battleState.player_pokemon.max_hp} level={100} types={battleState.player_pokemon.types} status_effects={battleState.player_pokemon.status_effects} showStatus={playerAnim.status} layout="status-only" hasSubstitute={(battleState.player_pokemon.substitute_hp ?? 0) > 0} />
            </div>
          </div>

          <div className="h-48 md:h-[220px] 2xl:h-[300px] gba-box flex flex-col justify-center relative gba-panel-shadow shrink-0">
            {gameOver ? (
              <div className="flex flex-col items-center justify-center h-full p-6 bg-black/60 text-center">
                <p className="text-[10px] md:text-3xl text-yellow-500 uppercase mb-4 md:mb-8 tracking-[0.2em] md:tracking-[0.3em] animate-pulse font-bold leading-relaxed md:leading-normal max-w-[90%]">{gameOver}</p>
                <button onClick={handleQuit} className="px-8 md:px-20 py-2 md:py-5 bg-red-900/40 border-2 md:border-4 border-red-800 text-white text-[8px] md:text-sm uppercase hover:bg-red-800 transition-all tracking-[0.2em] md:tracking-[0.3em] font-bold">RETURN HOME</button>
              </div>
            ) : showSwitchMenu ? (
              <div className="flex h-full animate-in fade-in zoom-in-95 duration-200">
                <div className="w-[70%] grid grid-cols-2 gap-4 p-4 md:p-6 items-center border-r-4 border-[#0f172a] overflow-y-auto custom-scrollbar">
                  {battleState.player_team?.map((p, i) => (
                    <button key={i} onClick={() => handleMove(undefined, i)} disabled={isProcessing || p.current_hp <= 0 || p.name === battleState.player_pokemon.name} className={`relative flex items-center gap-3 p-2 rounded-lg border-2 transition-all text-left ${p.name === battleState.player_pokemon.name ? 'border-yellow-500 bg-yellow-500/10 cursor-not-allowed' : 'border-slate-700 hover:border-white hover:bg-white/5'} ${p.current_hp <= 0 ? 'opacity-40 grayscale cursor-not-allowed' : ''}`}>
                      <div className="w-10 h-10 md:w-16 md:h-16 shrink-0"><img src={p.sprite} alt={p.name} className="w-full h-full object-contain" /></div>
                      <div className="flex flex-col gap-1 overflow-hidden">
                        <span className="text-[9px] md:text-[14px] uppercase truncate font-bold">{p.name}</span>
                        <div className="w-full h-1.5 md:h-2 bg-gray-800 rounded-full overflow-hidden border border-white/5">
                          <div className={`h-full transition-all duration-500 ${p.current_hp / p.max_hp > 0.5 ? 'bg-green-500' : p.current_hp / p.max_hp > 0.2 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${(p.current_hp / p.max_hp) * 100}%` }} />
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                <div className="w-[30%] flex flex-col">
                  <div className="flex-1 p-4 md:p-8 flex flex-col justify-center text-center"><p className="text-[10px] md:text-sm text-gray-400 uppercase tracking-widest">Select a Pokemon</p></div>
                  <button onClick={() => setShowSwitchMenu(false)} disabled={battleState.player_pokemon.current_hp <= 0} className={`h-12 md:h-20 border-t-4 border-[#0f172a] text-[10px] md:text-[14px] uppercase transition-all tracking-[0.2em] ${battleState.player_pokemon.current_hp <= 0 ? 'opacity-30 cursor-not-allowed text-gray-500' : 'text-red-400 hover:bg-red-400/10'}`}>CANCEL</button>
                </div>
              </div>
            ) : (
              <div className="flex h-full">
                <div className="w-[60%] md:w-[70%] grid grid-cols-2 gap-x-2 md:gap-x-8 gap-y-4 md:gap-y-8 p-4 md:p-10 items-center border-r-4 border-[#0f172a]">
                  {battleState.player_moves.map((move, i) => (
                    <button key={move.name} onClick={() => handleMove(move.name)} onMouseEnter={() => setHoveredMove(move)} onMouseLeave={() => setHoveredMove(null)} disabled={isProcessing || move.pp <= 0 || battleStage !== 'active'} className={`text-left text-[11px] md:text-[18px] 2xl:text-[24px] uppercase group flex items-center gap-2 md:gap-6 transition-all break-words line-clamp-2 md:line-clamp-none ${isProcessing || battleStage !== 'active' ? 'opacity-50' : 'hover:text-red-400 md:hover:translate-x-4'}`}>
                      <span className="hidden md:block opacity-0 group-hover:opacity-100 w-0 h-0 border-l-[12px] border-l-red-500 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent shrink-0" />
                      <span className="break-words">{move.name.replace('-', ' ')}</span>
                    </button>
                  ))}
                </div>
                <div className="w-[40%] md:w-[30%] flex flex-col bg-black/20 md:bg-black/40">
                  <div className="flex-1 p-4 md:p-8 flex flex-col justify-center gap-4 md:gap-8">
                    <div className="flex flex-col">
                      <span className="text-gray-500 text-[8px] md:text-[12px] 2xl:text-[16px] uppercase mb-1 md:mb-3 tracking-[0.2em]">Move Detail</span>
                      <div className="flex flex-col gap-2 md:gap-4">
                        <span className="text-white text-[12px] md:text-[20px] 2xl:text-[28px] tracking-widest font-bold whitespace-nowrap">{hoveredMove ? `${hoveredMove.pp}/${hoveredMove.max_pp} PP` : '--/--'}</span>
                        <span className={`text-[8px] md:text-[10px] 2xl:text-[18px] px-2 md:px-5 py-1 md:py-2 rounded-md inline-block text-center tracking-[0.3em] font-bold uppercase ${hoveredMove ? `type-${hoveredMove.type.toLowerCase()}` : 'bg-gray-800 text-gray-600'}`}>{hoveredMove ? hoveredMove.type : 'NONE'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex border-t-4 border-[#0f172a]">
                    <button onClick={() => setShowSwitchMenu(true)} disabled={isProcessing || battleStage !== 'active'} className="flex-1 h-12 md:h-20 text-[10px] md:text-[14px] uppercase text-blue-400 hover:text-white transition-all flex items-center justify-center gap-2 group hover:bg-blue-400/10 tracking-[0.2em] border-r-4 border-[#0f172a]">POKEMON</button>
                    <button onClick={() => setShowForfeitModal(true)} className="flex-1 h-12 md:h-20 text-[10px] md:text-[14px] uppercase text-gray-500 hover:text-white transition-all flex items-center justify-center gap-2 group hover:bg-white/5 tracking-[0.2em]">RUN</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

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
