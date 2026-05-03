'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { searchPokemon, getMoveset, getAllSets, startBattle } from '@/lib/api';
import PokemonCard from '@/components/PokemonCard';

export default function Home() {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [selectedPokemon, setSelectedPokemon] = useState<any>(null);
  const [availableSets, setAvailableSets] = useState<any[]>([]);
  const [currentSetIndex, setCurrentSetIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [pokedexEntry, setPokedexEntry] = useState('');
  const router = useRouter();
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setSuggestions([]);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async (val: string) => {
    setQuery(val);
    if (val.length > 1) {
      try {
        const response = await fetch(`https://pokeapi.co/api/v2/pokemon?limit=1000`);
        const data = await response.json();
        const matches = data.results.filter((p: any) => p.name.includes(val.toLowerCase())).slice(0, 5);
        setSuggestions(matches);
      } catch (err) {
        console.error(err);
      }
    } else {
      setSuggestions([]);
    }
  };

  const selectPokemon = async (name: string) => {
    setLoading(true);
    setSuggestions([]);
    setQuery(name);
    try {
      const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${name.toLowerCase()}`);
      const data = await response.json();
      setSelectedPokemon(data);

      const [speciesRes, setsRes] = await Promise.all([
        fetch(`https://pokeapi.co/api/v2/pokemon-species/${data.id}/`).then(res => res.json()),
        getAllSets(name)
      ]);

      const entry = speciesRes.flavor_text_entries.find((e: any) => e.language.name === 'en');
      setPokedexEntry(entry ? entry.flavor_text.replace(/\f/g, ' ').replace(/\n/g, ' ') : '');
      
      if (setsRes.success && setsRes.sets.length > 0) {
        setAvailableSets(setsRes.sets);
      } else {
        const movesRes = await getMoveset(name);
        setAvailableSets([{
          set_name: 'Default Set',
          moves: movesRes.moves || ['tackle', 'growl']
        }]);
      }
      setCurrentSetIndex(0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartBattle = async () => {
    if (!selectedPokemon) return;
    setLoading(true);
    try {
      const battleState = await startBattle(selectedPokemon.name, availableSets[currentSetIndex]);
      // Save battle state to local storage or state management to be used in /battle
      localStorage.setItem('initialBattleState', JSON.stringify(battleState));
      router.push('/battle');
    } catch (err) {
      console.error(err);
      alert('Failed to start battle');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-white font-retro overflow-x-hidden relative">
      {/* Dynamic Background Background */}
      <div className="absolute inset-0 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center opacity-20 blur-sm pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#020617]/50 via-transparent to-[#020617] pointer-events-none" />

      <header className="relative z-50 border-b border-white/5 backdrop-blur-md bg-[#020617]/40">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <img src="/images/pokeball.png" alt="Logo" className="w-10 h-10 animate-spin-slow" />
            <h1 className="text-lg md:text-2xl font-bold tracking-[0.15em] bg-gradient-to-r from-white via-yellow-400 to-white bg-clip-text text-transparent">
              POKÉSIM <span className="text-yellow-500">BATTLE</span>
            </h1>
          </div>
          <div className="flex items-center space-x-6">
            <a href="https://github.com/PerseusKyogre09" target="_blank" className="text-gray-500 hover:text-white transition-all text-[10px] uppercase tracking-widest hidden sm:block">
              [ GITHUB ]
            </a>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12 flex flex-col items-center">
        <div className="max-w-4xl w-full text-center mb-16 relative">
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-48 h-48 bg-yellow-500/10 blur-[100px] rounded-full pointer-events-none" />
          <h2 className="text-3xl md:text-6xl mb-8 leading-tight tracking-tighter" style={{ textShadow: '8px 8px 0 rgba(0,0,0,0.5)' }}>
            CHOOSE YOUR <br/>
            <span className="text-yellow-500">CHAMPION</span>
          </h2>
          <p className="text-gray-400 text-[10px] md:text-xs leading-relaxed uppercase tracking-[0.3em] opacity-80 max-w-xl mx-auto">
            Experience authentic high-stakes battles with precision movesets and modern GBA aesthetics.
          </p>
        </div>

        <div className="w-full max-w-lg relative mb-20" ref={searchRef}>
          <div className="relative group gba-panel-shadow">
            <input
              type="text"
              value={query}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="ENTER POKÉMON NAME..."
              className="w-full px-8 py-6 bg-gray-900/80 border-4 border-[#475569] text-xs md:text-sm focus:outline-none focus:border-yellow-500 transition-all placeholder:text-gray-700 font-retro tracking-widest text-white"
            />
            <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center space-x-4">
              {loading ? (
                <div className="w-6 h-6 border-4 border-yellow-500 border-t-transparent rounded-full animate-spin" />
              ) : (
                <img src="/images/pokeball.gif" alt="" className="w-8 h-8 opacity-40 group-hover:opacity-100 transition-opacity" />
              )}
            </div>
          </div>

          {suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900 border-4 border-gray-800 overflow-hidden shadow-2xl z-40 animate-in fade-in slide-in-from-top-2">
              {suggestions.map((p) => (
                <button
                  key={p.name}
                  onClick={() => selectPokemon(p.name)}
                  className="w-full text-left px-6 py-3 hover:bg-yellow-500 hover:text-gray-900 transition-colors capitalize font-retro text-[10px] border-b-2 border-gray-800 last:border-0"
                >
                  {p.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {selectedPokemon && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 w-full max-w-5xl animate-in fade-in zoom-in-95 duration-500">
            <div className="flex flex-col items-center">
              <PokemonCard
                name={selectedPokemon.name}
                sprite={selectedPokemon.sprites.other['official-artwork'].front_default || selectedPokemon.sprites.front_default}
                currentHp={selectedPokemon.stats[0].base_stat}
                maxHp={selectedPokemon.stats[0].base_stat}
                level={100}
                types={selectedPokemon.types.map((t: any) => t.type.name)}
              />
              
              <div className="mt-8 w-full max-w-sm">
                <button
                  onClick={handleStartBattle}
                  disabled={loading}
                  className="w-full py-5 bg-yellow-500 hover:bg-yellow-400 disabled:bg-gray-700 text-gray-900 font-retro text-xs border-4 border-yellow-600 transition-all shadow-[0_0_30px_rgba(234,179,8,0.2)] hover:shadow-[0_0_40px_rgba(234,179,8,0.4)] active:scale-95 flex items-center justify-center space-x-2"
                  style={{ clipPath: 'polygon(20px 0, 100% 0, 100% calc(100% - 20px), calc(100% - 20px) 100%, 0 100%, 0 20px)' }}
                >
                  <span>{loading ? 'PREPARING...' : 'START BATTLE'}</span>
                  {!loading && <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>}
                </button>
              </div>
            </div>

            <div className="space-y-8">
              <div className="bg-gray-900/50 backdrop-blur-md p-8 border-4 border-gray-800 shadow-xl relative">
                <div className="absolute top-0 left-0 w-4 h-4 bg-yellow-500/20" />
                <h3 className="text-yellow-500 font-retro uppercase tracking-widest text-[10px] mb-6 flex items-center">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse" />
                  Pokedex Entry
                </h3>
                <p className="text-xs font-retro leading-loose text-gray-300 italic opacity-90">
                  "{pokedexEntry || 'A mysterious Pokémon discovered in the wild...'}"
                </p>
              </div>

              <div className="bg-gray-900/50 backdrop-blur-md p-8 rounded-3xl border border-white/5 shadow-xl">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-yellow-500 font-bold uppercase tracking-widest text-sm">Moveset Selection</h3>
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => setCurrentSetIndex(Math.max(0, currentSetIndex - 1))}
                      disabled={currentSetIndex === 0}
                      className="w-8 h-8 flex items-center justify-center bg-white/5 hover:bg-white/10 rounded-full disabled:opacity-30"
                    >
                      ←
                    </button>
                    <span className="text-xs font-mono flex items-center px-2">{currentSetIndex + 1} / {availableSets.length}</span>
                    <button 
                      onClick={() => setCurrentSetIndex(Math.min(availableSets.length - 1, currentSetIndex + 1))}
                      disabled={currentSetIndex === availableSets.length - 1}
                      className="w-8 h-8 flex items-center justify-center bg-white/5 hover:bg-white/10 rounded-full disabled:opacity-30"
                    >
                      →
                    </button>
                  </div>
                </div>

                <div className="mb-6">
                   <p className="text-white font-bold text-lg mb-1">{availableSets[currentSetIndex]?.set_name}</p>
                   <p className="text-gray-500 text-sm uppercase tracking-wide">{availableSets[currentSetIndex]?.format || 'Standard'}</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {availableSets[currentSetIndex]?.moves.map((move: string) => (
                    <div key={move} className="bg-white/5 border border-white/5 px-4 py-3 rounded-xl text-sm font-medium capitalize">
                      {move.replace('-', ' ')}
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {selectedPokemon.stats.map((s: any) => (
                  <div key={s.stat.name} className="bg-gray-900/30 p-4 rounded-2xl border border-white/5">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs text-gray-500 uppercase font-bold">{s.stat.name.replace('special-', 'Sp.')}</span>
                      <span className="text-sm font-mono text-white">{s.base_stat}</span>
                    </div>
                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div className={`h-full bg-yellow-500/50`} style={{ width: `${(s.base_stat / 255) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="mt-24 py-12 border-t border-white/5 text-center text-gray-500">
        <p className="text-sm">Created with ❤️ by PerseusKyogre09 | Powered by PokeAPI</p>
      </footer>

      <style jsx global>{`
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
