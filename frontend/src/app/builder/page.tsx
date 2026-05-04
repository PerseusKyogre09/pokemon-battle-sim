'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  calculateHP,
  calculateOtherStat,
  NATURES,
  TYPE_COLORS,
  StatName,
  getNatureMultiplier
} from '@/lib/pokemon-utils';
import { API_BASE_URL, getAllSets, startBattle } from '@/lib/api';

// --- Types ---
interface TeamMember {
  id: string;
  species: string;
  nickname: string;
  level: number;
  gender: 'M' | 'F' | 'N';
  shiny: boolean;
  item: string;
  ability: string;
  teraType: string;
  moves: string[];
  evs: Record<StatName, number>;
  ivs: Record<StatName, number>;
  nature: string;
  baseStats: Record<StatName, number>;
  types: string[];
  sprite: string;
  allSprites: any;
  availableAbilities: string[];
  availableMoves: string[];
}

const DEFAULT_STATS: Record<StatName, number> = {
  hp: 100, attack: 100, defense: 100, spAtk: 100, spDef: 100, speed: 100
};

const DEFAULT_MEMBER: TeamMember = {
  id: '1',
  species: 'Pikachu',
  nickname: '',
  level: 100,
  gender: 'M',
  shiny: false,
  item: '',
  ability: 'Static',
  teraType: 'Electric',
  moves: ['', '', '', ''],
  evs: { hp: 0, attack: 0, defense: 0, spAtk: 0, spDef: 0, speed: 0 },
  ivs: { hp: 31, attack: 31, defense: 31, spAtk: 31, spDef: 31, speed: 31 },
  nature: 'Serious',
  baseStats: { ...DEFAULT_STATS },
  types: ['electric'],
  sprite: 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/25.gif',
  allSprites: null,
  availableAbilities: ['Static', 'Lightning Rod'],
  availableMoves: []
};

const STAT_LABELS: Record<StatName, string> = {
  hp: 'HP', attack: 'Atk', defense: 'Def', spAtk: 'SpA', spDef: 'SpD', speed: 'Spe'
};

const POKEMON_TYPES = Object.keys(TYPE_COLORS);

// --- Component ---
export default function PokemonBuilder() {
  const [team, setTeam] = useState<TeamMember[]>([{ ...DEFAULT_MEMBER }]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [allMoves, setAllMoves] = useState<string[]>([]);
  const [allItems, setAllItems] = useState<string[]>([]);
  const [allAbilities, setAllAbilities] = useState<string[]>([]);
  const [smogonSets, setSmogonSets] = useState<any[]>([]);
  const [allSpecies, setAllSpecies] = useState<any[]>([]);

  const currentMon = team[activeIndex];
  const router = useRouter();

  // Load basic data
  useEffect(() => {
    // In a real app, we'd fetch these once and cache
    const fetchCommonData = async () => {
      try {
        const [itemsRes, speciesRes] = await Promise.all([
          fetch('https://pokeapi.co/api/v2/item?limit=2000').then(r => r.json()),
          fetch('https://pokeapi.co/api/v2/pokemon-species?limit=1000').then(r => r.json())
        ]);
        setAllItems(itemsRes.results.map((i: any) => i.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())));
        setAllSpecies(speciesRes.results);
      } catch (e) {
        console.error("Failed to fetch common data", e);
      }
    };
    fetchCommonData();
  }, []);

  // Fetch Smogon Sets when species changes
  useEffect(() => {
    const loadSets = async () => {
      if (!currentMon.species) return;
      try {
        const data = await getAllSets(currentMon.species);
        if (data.success) {
          setSmogonSets(data.sets);
        } else {
          setSmogonSets([]);
        }
      } catch (e) {
        setSmogonSets([]);
      }
    };
    loadSets();
  }, [currentMon.species]);

  const updateCurrentMon = (updates: Partial<TeamMember>) => {
    setTeam(prev => {
      const newTeam = [...prev];
      newTeam[activeIndex] = { ...newTeam[activeIndex], ...updates };
      return newTeam;
    });
  };

  const handleSpeciesSearch = (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    const filtered = allSpecies
      .filter((p: any) => p.name.includes(q.toLowerCase()))
      .slice(0, 10);
    setSearchResults(filtered);
  };

  const selectSpecies = async (speciesName: string) => {
    try {
      const res = await fetch(`https://pokeapi.co/api/v2/pokemon/${speciesName}`);
      const data = await res.json();

      const stats: Record<StatName, number> = {
        hp: data.stats[0].base_stat,
        attack: data.stats[1].base_stat,
        defense: data.stats[2].base_stat,
        spAtk: data.stats[3].base_stat,
        spDef: data.stats[4].base_stat,
        speed: data.stats[5].base_stat,
      };

      // Priority: Gen 5 Animated > Gen 5 Static > Default Front
      const gen5 = data.sprites.versions?.['generation-v']?.['black-white'];
      const animated = gen5?.animated?.front_default;
      const static_gen5 = gen5?.front_default;
      const fallback = data.sprites.front_default;

      const spriteUrl = animated || static_gen5 || fallback || data.sprites.other['official-artwork'].front_default;

      updateCurrentMon({
        species: data.name.charAt(0).toUpperCase() + data.name.slice(1),
        baseStats: stats,
        types: data.types.map((t: any) => t.type.name),
        sprite: spriteUrl,
        allSprites: data.sprites,
        availableAbilities: data.abilities.map((a: any) => a.ability.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())),
        availableMoves: data.moves.map((m: any) => m.move.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())).sort(),
        ability: data.abilities[0].ability.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        moves: ['', '', '', ''],
        teraType: data.types[0].type.name.charAt(0).toUpperCase() + data.types[0].type.name.slice(1)
      });
      setSearchQuery('');
      setSearchResults([]);
    } catch (e) {
      console.error(e);
    }
  };

  const isAbilityValid = currentMon.ability === '' || currentMon.availableAbilities.includes(currentMon.ability);
  const invalidMoves = currentMon.moves.filter(m => m && m.trim() !== '' && !currentMon.availableMoves.includes(m));
  const isItemValid = currentMon.item === '' || allItems.includes(currentMon.item);
  // Lax validation: Only requires species to be selected
  const isMonValid = currentMon.species !== '';

  const applySmogonSet = (set: any) => {
    const newEvs = { hp: 0, attack: 0, defense: 0, spAtk: 0, spDef: 0, speed: 0 };
    if (set.evs) {
      Object.entries(set.evs).forEach(([stat, val]) => {
        const key = stat.toLowerCase() as StatName;
        if (key in newEvs) newEvs[key] = val as number;
        // Handle Smogon stat names
        if (stat === 'atk') newEvs.attack = val as number;
        if (stat === 'def') newEvs.defense = val as number;
        if (stat === 'spa') newEvs.spAtk = val as number;
        if (stat === 'spd') newEvs.spDef = val as number;
        if (stat === 'spe') newEvs.speed = val as number;
      });
    }

    updateCurrentMon({
      item: set.item || '',
      ability: set.ability || currentMon.ability,
      nature: set.nature || 'Serious',
      moves: set.moves.length > 0 ? set.moves : currentMon.moves,
      evs: newEvs
    });
  };

  const finalStats = useMemo(() => {
    const stats: Record<StatName, number> = { ...DEFAULT_STATS };
    Object.keys(currentMon.baseStats).forEach((key) => {
      const s = key as StatName;
      if (s === 'hp') {
        stats[s] = calculateHP(currentMon.baseStats[s], currentMon.ivs[s], currentMon.evs[s], currentMon.level, currentMon.species);
      } else {
        stats[s] = calculateOtherStat(currentMon.baseStats[s], currentMon.ivs[s], currentMon.evs[s], currentMon.level, currentMon.nature, s);
      }
    });
    return stats;
  }, [currentMon]);

  const totalEVs = Object.values(currentMon.evs).reduce((a, b) => a + b, 0);

  return (
    <div className="min-h-screen bg-[#020617] text-white font-retro overflow-x-hidden relative selection:bg-yellow-500/30">
      {/* Background FX */}
      <div className="fixed inset-0 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center opacity-10 blur-md pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-br from-[#020617] via-slate-900/80 to-[#020617] pointer-events-none" />

      {/* Dynamic Animated Particles or Glows */}
      <div className="fixed top-[-10%] right-[-10%] w-[50%] h-[50%] bg-yellow-500/10 rounded-full blur-[120px] animate-pulse pointer-events-none" />
      <div className="fixed bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[100px] animate-pulse pointer-events-none" />

      {/* Header */}
      <header className="sticky top-0 z-[100] border-b border-white/5 backdrop-blur-xl bg-slate-900/40">
        <div className="container mx-auto px-4 py-3 flex flex-wrap justify-between items-center gap-4">
          <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-all active:scale-95 group">
            <div className="relative">
              <img src="/images/pokeball.png" alt="Logo" className="w-8 h-8 md:w-10 md:h-10 animate-spin-slow group-hover:rotate-[360deg] transition-transform duration-1000" />
              <div className="absolute inset-0 bg-yellow-400/20 blur-lg rounded-full" />
            </div>
            <h1 className="text-lg md:text-2xl font-bold tracking-[0.1em] bg-gradient-to-r from-white via-yellow-400 to-white bg-clip-text text-transparent">
              POKÉ<span className="text-yellow-500">LAB</span>
            </h1>
          </Link>

          {/* Team Tabs */}
          <div className="flex items-center space-x-1 bg-black/40 p-1 rounded-xl border border-white/5">
            {team.map((mon, idx) => (
              <button
                key={mon.id}
                onClick={() => setActiveIndex(idx)}
                className={`px-4 py-2 rounded-lg text-[10px] uppercase tracking-tighter transition-all flex items-center gap-2 ${activeIndex === idx
                  ? 'bg-yellow-500 text-slate-900 font-bold shadow-lg shadow-yellow-500/20'
                  : 'hover:bg-white/5 text-gray-400'
                  }`}
              >
                <div className={`w-2 h-2 rounded-full ${activeIndex === idx ? 'bg-slate-900' : 'bg-gray-600'}`} />
                {mon.species || 'Empty'}
              </button>
            ))}
            <button
              disabled
              className="w-10 h-10 flex items-center justify-center text-gray-600 cursor-not-allowed hover:text-gray-400 transition-colors"
              title="Team management disabled in preview"
            >
              +
            </button>
          </div>

          <div className="hidden lg:block text-gray-500 text-[9px] uppercase tracking-[0.4em] font-light">
            [ TEAM BUILDER ]
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 relative z-10">
        <div className="max-w-7xl mx-auto">

          {/* Top Section: Species Search & Identity */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">

            {/* Search Panel */}
            <div className="lg:col-span-4 space-y-6">
              <div className="glass-panel p-6 rounded-3xl relative z-[100] group">
                <div className="absolute top-0 left-0 w-1 h-full bg-yellow-500 opacity-50" />
                <label className="text-yellow-500 font-bold uppercase text-[9px] tracking-[0.2em] block mb-4">
                  Species Lookup
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleSpeciesSearch(e.target.value)}
                    className="w-full px-4 py-3 builder-input rounded-xl text-[11px] placeholder:text-slate-600"
                    placeholder="Search any Pokemon..."
                  />
                  {searchResults.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 glass-panel rounded-xl border border-yellow-500/30 overflow-hidden z-[200] shadow-2xl">
                      {searchResults.map((p) => (
                        <button
                          key={p.name}
                          onClick={() => selectSpecies(p.name)}
                          className="w-full px-4 py-3 text-left hover:bg-yellow-500 hover:text-slate-900 transition-colors text-[10px] uppercase font-bold border-b border-white/5 last:border-0"
                        >
                          {p.name.replace(/-/g, ' ')}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Central Identity Panel */}
            <div className="lg:col-span-8 glass-panel p-8 rounded-3xl grid grid-cols-1 md:grid-cols-2 gap-8 items-center relative overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none select-none p-12 overflow-hidden z-0">
                <h1 
                  className="font-black uppercase italic whitespace-nowrap leading-none tracking-tighter"
                  style={{ fontSize: `${Math.min(120, 900 / Math.max(currentMon.species.length, 1))}px` }}
                >
                  {currentMon.species}
                </h1>
              </div>

              {/* Sprite Visualizer */}
              <div className="flex flex-col items-center justify-center space-y-6">
                <div className="relative w-48 h-48 md:w-64 md:h-64 flex items-center justify-center">
                  <div className={`absolute inset-0 bg-gradient-to-b from-transparent to-black/20 rounded-full blur-2xl ${currentMon.shiny ? 'bg-yellow-500/5' : ''}`} />
                  <img
                    src={(() => {
                      if (!currentMon.allSprites) return currentMon.sprite;

                      const s = currentMon.allSprites;
                      const gen5 = s.versions?.['generation-v']?.['black-white'];

                      if (currentMon.shiny) {
                        return gen5?.animated?.front_shiny || gen5?.front_shiny || s.front_shiny || currentMon.sprite;
                      }
                      return gen5?.animated?.front_default || gen5?.front_default || s.front_default || currentMon.sprite;
                    })()}
                    alt={currentMon.species}
                    className="w-full h-full object-contain relative z-10 transition-transform duration-500 hover:scale-110 drop-shadow-[0_20px_50px_rgba(0,0,0,0.5)]"
                    style={{ imageRendering: 'pixelated' }}
                  />
                  {currentMon.shiny && (
                    <div className="absolute inset-0 z-20 pointer-events-none flex items-center justify-center">
                      <div className="w-full h-full animate-pulse bg-yellow-400/10 blur-3xl opacity-30" />
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  {currentMon.types.map(t => (
                    <span
                      key={t}
                      className="px-4 py-1.5 rounded-full text-[9px] uppercase font-bold tracking-widest shadow-lg"
                      style={{ backgroundColor: TYPE_COLORS[t] || '#777', textShadow: '1px 1px 2px rgba(0,0,0,0.5)' }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              {/* Identity Controls */}
              <div className="space-y-5">
                <div>
                  <label className="text-gray-500 text-[8px] uppercase tracking-widest block mb-2">Nickname</label>
                  <input
                    type="text"
                    value={currentMon.nickname}
                    onChange={(e) => updateCurrentMon({ nickname: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-[10px] focus:border-yellow-500 outline-none"
                    placeholder={currentMon.species}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-gray-500 text-[8px] uppercase tracking-widest block mb-2">Level</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={currentMon.level}
                      onChange={(e) => updateCurrentMon({ level: parseInt(e.target.value) || 100 })}
                      className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-[10px] focus:border-yellow-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-gray-500 text-[8px] uppercase tracking-widest block mb-2">Tera Type</label>
                    <select
                      value={currentMon.teraType}
                      onChange={(e) => updateCurrentMon({ teraType: e.target.value })}
                      className="w-full px-3 py-2 bg-[#1e293b] border border-white/10 rounded-lg text-[10px] outline-none"
                    >
                      {POKEMON_TYPES.map(t => (
                        <option key={t} value={t}>{t.toUpperCase()}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2">
                  <div className="flex gap-3">
                    <button
                      onClick={() => updateCurrentMon({ gender: 'M' })}
                      className={`w-8 h-8 flex items-center justify-center rounded-lg border transition-all ${currentMon.gender === 'M' ? 'bg-blue-500 border-blue-400' : 'bg-white/5 border-white/10 text-gray-500'}`}
                    >
                      ♂
                    </button>
                    <button
                      onClick={() => updateCurrentMon({ gender: 'F' })}
                      className={`w-8 h-8 flex items-center justify-center rounded-lg border transition-all ${currentMon.gender === 'F' ? 'bg-pink-500 border-pink-400' : 'bg-white/5 border-white/10 text-gray-500'}`}
                    >
                      ♀
                    </button>
                  </div>
                  <button
                    onClick={() => updateCurrentMon({ shiny: !currentMon.shiny })}
                    className={`px-4 py-2 rounded-lg border transition-all text-[9px] uppercase font-bold ${currentMon.shiny ? 'bg-yellow-500 border-yellow-400 text-slate-900' : 'bg-white/5 border-white/10 text-gray-500'}`}
                  >
                    ★ SHINY
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Section: Equipment & Moves */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">

            {/* Equipment: Item & Ability */}
            <div className="glass-panel p-8 rounded-3xl space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-yellow-500 font-bold uppercase text-[9px] tracking-[0.2em] block mb-3">Ability</label>
                  <select
                    value={currentMon.ability}
                    onChange={(e) => updateCurrentMon({ ability: e.target.value })}
                    className={`w-full px-4 py-3 bg-[#1e293b] border rounded-xl text-[10px] outline-none transition-all ${isAbilityValid ? 'border-white/10 focus:border-yellow-500' : 'border-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]'}`}
                  >
                    <option value="" disabled>Select Ability...</option>
                    <optgroup label="Species Abilities">
                      {currentMon.availableAbilities.map(a => <option key={`avail-${a}`} value={a}>{a}</option>)}
                    </optgroup>
                  </select>
                  {!isAbilityValid && <p className="text-red-500 text-[7px] mt-1 uppercase tracking-widest animate-pulse">Illegal Ability</p>}
                </div>
                <div>
                  <label className="text-yellow-500 font-bold uppercase text-[9px] tracking-[0.2em] block mb-3">Held Item</label>
                  <input
                    list="items"
                    type="text"
                    value={currentMon.item}
                    onChange={(e) => updateCurrentMon({ item: e.target.value })}
                    className={`w-full px-4 py-3 bg-white/5 border rounded-xl text-[10px] outline-none transition-all ${isItemValid ? 'border-white/10 focus:border-yellow-500' : 'border-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]'}`}
                    placeholder="Select Item..."
                  />
                  <datalist id="items">
                    {allItems.slice(0, 1000).map(i => <option key={i} value={i} />)}
                  </datalist>
                  {!isItemValid && <p className="text-red-500 text-[7px] mt-1 uppercase tracking-widest animate-pulse">Invalid Item</p>}
                </div>
              </div>
            </div>

            {/* Moves: 4 Slots */}
            <div className="glass-panel p-8 rounded-3xl">
              <label className="text-yellow-500 font-bold uppercase text-[9px] tracking-[0.2em] block mb-4">Moveset</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[0, 1, 2, 3].map(i => {
                  const move = currentMon.moves[i] || '';
                  const isMoveValid = move === '' || currentMon.availableMoves.includes(move);
                  return (
                    <div key={i} className="relative group">
                      <input
                        list={`moves-${currentMon.id}`}
                        type="text"
                        value={move}
                        onChange={(e) => {
                          const newMoves = [...currentMon.moves];
                          newMoves[i] = e.target.value;
                          updateCurrentMon({ moves: newMoves });
                        }}
                        className={`w-full px-4 py-4 bg-white/5 border rounded-2xl text-[10px] outline-none transition-all uppercase font-bold placeholder:text-gray-700 ${isMoveValid ? 'border-white/10 focus:border-yellow-500' : 'border-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]'}`}
                        placeholder={`MOVE ${i + 1}`}
                      />
                      <div className={`absolute right-3 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full transition-colors ${isMoveValid ? 'bg-white/20 group-hover:bg-yellow-500' : 'bg-red-500 animate-pulse'}`} />
                    </div>
                  );
                })}
                <datalist id={`moves-${currentMon.id}`}>
                  {currentMon.availableMoves.map(m => <option key={m} value={m} />)}
                </datalist>
              </div>
            </div>
          </div>

          {/* Smogon Builds: Quick Importer */}
          {smogonSets.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-4 mb-4">
                <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-white/10" />
                <h3 className="text-blue-400 font-bold uppercase text-[9px] tracking-[0.3em]">Quick Build Importer</h3>
                <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-white/10" />
              </div>
              <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                {smogonSets.map((set, i) => (
                  <button
                    key={i}
                    onClick={() => applySmogonSet(set)}
                    className="min-w-[200px] flex-shrink-0 p-4 bg-slate-900/60 border border-white/5 hover:border-blue-500/40 hover:bg-blue-500/10 rounded-2xl text-left transition-all group backdrop-blur-md"
                  >
                    <div className="text-[10px] font-bold text-white group-hover:text-blue-400 uppercase truncate">{set.set_name}</div>
                    <div className="text-[7px] text-gray-500 uppercase mt-1">{set.format}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Section: Stats Laboratory */}
          <div className="glass-panel p-8 rounded-3xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 flex items-center gap-2 opacity-50">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-[0.3em]">EV POOL:</span>
              <span className={`text-[14px] font-mono font-bold ${totalEVs > 510 ? 'text-red-500' : 'text-green-400'}`}>
                {510 - totalEVs}
              </span>
            </div>

            <div className="mb-10">
              <label className="text-yellow-500 font-bold uppercase text-[11px] tracking-[0.3em] block mb-2">Stats Laboratory</label>
              <p className="text-[8px] text-gray-500 uppercase tracking-widest italic">Precision Tuning for Competitive Excellence</p>
            </div>

            <div className="space-y-8 max-w-5xl mx-auto">
              <div className="grid grid-cols-12 gap-4 text-[9px] text-gray-500 font-bold uppercase tracking-[0.2em] mb-4 border-b border-white/5 pb-2">
                <div className="col-span-2">Stat</div>
                <div className="col-span-1 text-center">Base</div>
                <div className="col-span-5 text-center">Effort Values (EVs)</div>
                <div className="col-span-2 text-center">Individual Values (IVs)</div>
                <div className="col-span-2 text-right">Final</div>
              </div>

              {(Object.keys(currentMon.baseStats) as StatName[]).map((stat) => {
                const multiplier = getNatureMultiplier(currentMon.nature, stat);
                const isPlus = multiplier > 1;
                const isMinus = multiplier < 1;

                return (
                  <div key={stat} className="grid grid-cols-12 gap-4 items-center group">
                    {/* Name */}
                    <div className={`col-span-2 text-[10px] font-bold uppercase ${isPlus ? 'text-red-400' : isMinus ? 'text-blue-400' : 'text-white'}`}>
                      {STAT_LABELS[stat]} {isPlus ? '↑' : isMinus ? '↓' : ''}
                    </div>

                    {/* Base */}
                    <div className="col-span-1 text-center">
                      <input
                        type="number"
                        min="1"
                        max="255"
                        value={currentMon.baseStats[stat]}
                        onChange={(e) => {
                          const val = Math.max(1, parseInt(e.target.value) || 1);
                          const newBase = { ...currentMon.baseStats, [stat]: val };
                          updateCurrentMon({ baseStats: newBase });
                        }}
                        className="w-12 px-1 py-1 bg-white/5 border border-white/10 rounded text-[9px] text-center font-mono text-gray-400 focus:border-yellow-500 outline-none"
                      />
                    </div>

                    {/* EV Slider & Input */}
                    <div className="col-span-5 flex items-center gap-4">
                      <div className="flex-1 stat-bar-bg relative">
                        <div
                          className="stat-bar-fill bg-yellow-500 shadow-[0_0_15px_rgba(234,179,8,0.5)]"
                          style={{ width: `${(currentMon.evs[stat] / 252) * 100}%` }}
                        />
                        <input
                          type="range"
                          min="0"
                          max="252"
                          step="4"
                          value={currentMon.evs[stat]}
                          onChange={(e) => {
                            const val = parseInt(e.target.value);
                            const newEvs = { ...currentMon.evs, [stat]: val };
                            updateCurrentMon({ evs: newEvs });
                          }}
                          className="absolute inset-0 w-full stat-slider opacity-0 group-hover:opacity-100 transition-opacity"
                        />
                      </div>
                      <input
                        type="number"
                        min="0"
                        max="252"
                        value={currentMon.evs[stat]}
                        onChange={(e) => {
                          const val = Math.min(252, parseInt(e.target.value) || 0);
                          const newEvs = { ...currentMon.evs, [stat]: val };
                          updateCurrentMon({ evs: newEvs });
                        }}
                        className="w-14 px-2 py-1 bg-black/40 border border-white/10 rounded text-[10px] text-center font-mono outline-none focus:border-yellow-500"
                      />
                    </div>

                    {/* IV Slider & Input */}
                    <div className="col-span-2 flex items-center gap-3">
                      <div className="flex-1 stat-bar-bg relative">
                        <div
                          className="stat-bar-fill bg-blue-500/50"
                          style={{ width: `${(currentMon.ivs[stat] / 31) * 100}%` }}
                        />
                        <input
                          type="range"
                          min="0"
                          max="31"
                          value={currentMon.ivs[stat]}
                          onChange={(e) => {
                            const val = parseInt(e.target.value);
                            const newIvs = { ...currentMon.ivs, [stat]: val };
                            updateCurrentMon({ ivs: newIvs });
                          }}
                          className="absolute inset-0 w-full stat-slider opacity-0 group-hover:opacity-100 transition-opacity"
                        />
                      </div>
                      <input
                        type="number"
                        min="0"
                        max="31"
                        value={currentMon.ivs[stat]}
                        onChange={(e) => {
                          const val = Math.min(31, parseInt(e.target.value) || 0);
                          const newIvs = { ...currentMon.ivs, [stat]: val };
                          updateCurrentMon({ ivs: newIvs });
                        }}
                        className="w-8 px-1 py-1 bg-black/40 border border-white/10 rounded text-[9px] text-center font-mono outline-none focus:border-blue-500"
                      />
                    </div>

                    {/* Final Stat */}
                    <div className="col-span-2 text-right text-[12px] font-mono font-bold text-yellow-500">
                      {finalStats[stat]}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Nature Selection */}
            <div className="mt-12 pt-8 border-t border-white/5 flex flex-wrap items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <label className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">Nature:</label>
                <select
                  value={currentMon.nature}
                  onChange={(e) => updateCurrentMon({ nature: e.target.value })}
                  className="px-4 py-2 bg-[#1e293b] border border-white/10 rounded-xl text-[10px] outline-none focus:border-yellow-500 appearance-none min-w-[150px]"
                >
                  {Object.keys(NATURES).map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>

              <div className="text-[8px] text-gray-500 uppercase tracking-widest flex items-center gap-4">
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-400" /> Boosted (+10%)</div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-400" /> Hindered (-10%)</div>
              </div>
            </div>
          </div>

          {/* Action Footer */}
          <div className="mt-12 flex flex-col sm:flex-row gap-6 justify-center items-center pb-16">
            <Link
              href="/"
              className="px-10 py-4 glass-panel border border-white/10 hover:border-white/20 rounded-2xl text-[11px] uppercase tracking-[0.2em] font-bold text-gray-400 hover:text-white transition-all active:scale-95"
            >
              Discard Project
            </Link>
            <button
              onClick={async () => {
                setIsSearching(true);
                try {
                  const formattedMoves = currentMon.moves.filter(m => m && m.trim() !== '').map(m => m.toLowerCase().replace(/ /g, '-'));
                  const selectedSet = {
                    moves: formattedMoves,
                    ability: currentMon.ability.toLowerCase().replace(/ /g, '-'),
                    item: currentMon.item.toLowerCase().replace(/ /g, '-'),
                    nature: currentMon.nature,
                    evs: currentMon.evs,
                    ivs: currentMon.ivs
                  };

                  const battleState = await startBattle(currentMon.species.toLowerCase(), selectedSet, 'random');
                  localStorage.setItem('initialBattleState', JSON.stringify(battleState));
                  router.push('/battle');
                } catch (e) {
                  console.error(e);
                  alert('Failed to initialize battle sequence.');
                } finally {
                  setIsSearching(false);
                }
              }}
              disabled={isSearching || !isMonValid}
              className={`px-12 py-5 bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-400 hover:to-amber-500 text-slate-900 rounded-2xl text-[12px] uppercase font-bold tracking-[0.2em] shadow-[0_10px_30px_rgba(234,179,8,0.3)] hover:shadow-[0_15px_40px_rgba(234,179,8,0.5)] transition-all active:scale-95 group ${isSearching || !isMonValid ? 'opacity-50 cursor-not-allowed grayscale' : ''}`}
            >
              {isSearching ? 'SYNCING DATA...' : !isMonValid ? 'Illegal Build' : 'Initialize Battle'} <span className="ml-2 group-hover:translate-x-1 transition-transform inline-block">→</span>
            </button>
          </div>

        </div>
      </main>

      {/* Retro HUD Decoration */}
      <div className="fixed bottom-4 left-4 text-[7px] text-gray-600 font-mono tracking-widest select-none pointer-events-none uppercase">
        System: Online | Latency: 24ms | Session: {Math.random().toString(36).substring(7).toUpperCase()}
      </div>
    </div>
  );
}
