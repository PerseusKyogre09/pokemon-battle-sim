'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const PokemonTypes = [
  'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice', 'Fighting', 'Poison',
  'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy'
];

const AllMoves = [
  'Tackle', 'Thunderbolt', 'Flamethrower', 'Ice Beam', 'Psychic', 'Dragon Claw',
  'Earthquake', 'Stone Edge', 'Close Combat', 'Shadow Ball', 'Dark Pulse', 'Iron Head',
  'Flash Cannon', 'Power Whip', 'Hydro Pump', 'Surf', 'Blizzard', 'Hurricane',
  'Meteor Mash', 'Outrage', 'Icicle Spear', 'Volt Switch', 'Fire Punch', 'Ice Punch',
  'Thunderpunch', 'Earthquake', 'Stone Edge', 'Crunch', 'Aerial Ace'
];

export default function PokemonBuilder() {
  const [pokemonName, setPokemonName] = useState('CustomMon');
  const [baseStats, setBaseStats] = useState({
    hp: 100,
    attack: 100,
    defense: 100,
    spAtk: 100,
    spDef: 100,
    speed: 100
  });
  const [type1, setType1] = useState('Normal');
  const [type2, setType2] = useState('Normal');
  const [ability, setAbility] = useState('Static');
  const [selectedMoves, setSelectedMoves] = useState(['Tackle', 'Growl', 'Thundershock', 'Spark']);
  const router = useRouter();

  const handleStatChange = (stat: keyof typeof baseStats, value: number) => {
    setBaseStats(prev => ({
      ...prev,
      [stat]: Math.max(1, Math.min(255, value))
    }));
  };

  const handleMoveSelect = (move: string) => {
    if (selectedMoves.includes(move)) {
      setSelectedMoves(selectedMoves.filter(m => m !== move));
    } else if (selectedMoves.length < 4) {
      setSelectedMoves([...selectedMoves, move]);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-white font-retro overflow-x-hidden relative">
      {/* Dynamic Background */}
      <div className="absolute inset-0 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center opacity-20 blur-sm pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#020617]/50 via-transparent to-[#020617] pointer-events-none" />

      <header className="relative z-50 border-b border-white/5 backdrop-blur-md bg-[#020617]/40">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-4 hover:opacity-80 transition-opacity">
            <img src="/images/pokeball.png" alt="Logo" className="w-10 h-10 animate-spin-slow" />
            <h1 className="text-lg md:text-2xl font-bold tracking-[0.15em] bg-gradient-to-r from-white via-yellow-400 to-white bg-clip-text text-transparent">
              POKÉSIM <span className="text-yellow-500">BATTLE</span>
            </h1>
          </Link>
          <div className="text-gray-500 text-[10px] uppercase tracking-widest">
            [ BUILDER ]
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12 relative z-10">
        <div className="max-w-5xl mx-auto">
          {/* Page Title */}
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl mb-4 tracking-tighter" style={{ textShadow: '8px 8px 0 rgba(0,0,0,0.5)' }}>
              BUILD YOUR <br />
              <span className="text-yellow-500">CUSTOM MON</span>
            </h2>
            <p className="text-gray-400 text-[10px] md:text-xs uppercase tracking-[0.3em]">
              Design your perfect Pokémon champion
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* LEFT: Basic Info & Stats */}
            <div className="space-y-6">
              {/* Pokemon Name */}
              <div className="bg-gray-900/50 backdrop-blur-md p-6 rounded-3xl border border-white/5 shadow-xl">
                <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-sm tracking-widest block mb-3">
                  Pokémon Name
                </label>
                <input
                  type="text"
                  value={pokemonName}
                  onChange={(e) => setPokemonName(e.target.value)}
                  maxLength={20}
                  className="w-full px-4 py-3 bg-gray-800/50 border-2 border-gray-700 rounded-lg text-white font-retro focus:outline-none focus:border-yellow-500 transition-colors"
                  placeholder="Enter custom name..."
                />
              </div>

              {/* Types */}
              <div className="bg-gray-900/50 backdrop-blur-md p-6 rounded-3xl border border-white/5 shadow-xl">
                <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-sm tracking-widest block mb-4">
                  Types
                </label>
                <div className="space-y-3">
                  <div>
                    <p className="text-[8px] text-gray-400 uppercase mb-2">Primary Type</p>
                    <select
                      value={type1}
                      onChange={(e) => setType1(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-800/50 border-2 border-gray-700 rounded-lg text-white font-retro focus:outline-none focus:border-yellow-500 text-[9px]"
                    >
                      {PokemonTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <p className="text-[8px] text-gray-400 uppercase mb-2">Secondary Type</p>
                    <select
                      value={type2}
                      onChange={(e) => setType2(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-800/50 border-2 border-gray-700 rounded-lg text-white font-retro focus:outline-none focus:border-yellow-500 text-[9px]"
                    >
                      {PokemonTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Ability */}
              <div className="bg-gray-900/50 backdrop-blur-md p-6 rounded-3xl border border-white/5 shadow-xl">
                <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-sm tracking-widest block mb-3">
                  Ability
                </label>
                <input
                  type="text"
                  value={ability}
                  onChange={(e) => setAbility(e.target.value)}
                  maxLength={30}
                  className="w-full px-4 py-3 bg-gray-800/50 border-2 border-gray-700 rounded-lg text-white font-retro focus:outline-none focus:border-yellow-500 transition-colors"
                  placeholder="Enter ability name..."
                />
              </div>
            </div>

            {/* RIGHT: Base Stats */}
            <div className="bg-gray-900/50 backdrop-blur-md p-6 rounded-3xl border border-white/5 shadow-xl h-fit">
              <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-sm tracking-widest block mb-4">
                Base Stats
              </label>
              <div className="space-y-4">
                {[
                  { label: 'HP', key: 'hp' },
                  { label: 'ATK', key: 'attack' },
                  { label: 'DEF', key: 'defense' },
                  { label: 'SP.ATK', key: 'spAtk' },
                  { label: 'SP.DEF', key: 'spDef' },
                  { label: 'SPD', key: 'speed' }
                ].map(({ label, key }) => (
                  <div key={key}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[8px] uppercase text-gray-400 font-bold">{label}</span>
                      <span className="text-[10px] font-mono text-yellow-500">{baseStats[key as keyof typeof baseStats]}</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="255"
                      value={baseStats[key as keyof typeof baseStats]}
                      onChange={(e) => handleStatChange(key as keyof typeof baseStats, parseInt(e.target.value))}
                      className="w-full h-1.5 bg-gray-800 rounded-full appearance-none cursor-pointer accent-yellow-500"
                    />
                  </div>
                ))}
                <div className="mt-6 pt-4 border-t border-white/10">
                  <div className="flex justify-between items-center">
                    <span className="text-[8px] uppercase text-gray-400 font-bold">Total</span>
                    <span className="text-[12px] font-mono text-yellow-500 font-bold">
                      {Object.values(baseStats).reduce((a, b) => a + b, 0)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Moves Section */}
          <div className="mt-8 bg-gray-900/50 backdrop-blur-md p-6 rounded-3xl border border-white/5 shadow-xl">
            <div className="mb-6">
              <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-sm tracking-widest block mb-4">
                Moves (Select up to 4)
              </label>
              <p className="text-[8px] text-gray-400 uppercase mb-4">Selected: {selectedMoves.length}/4</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 md:gap-3">
              {AllMoves.map(move => (
                <button
                  key={move}
                  onClick={() => handleMoveSelect(move)}
                  className={`px-3 py-2 md:py-3 rounded-lg border-2 transition-all text-[8px] md:text-[9px] font-retro uppercase tracking-wider ${
                    selectedMoves.includes(move)
                      ? 'bg-yellow-500 border-yellow-600 text-gray-900 font-bold'
                      : 'bg-gray-800/50 border-gray-700 text-gray-300 hover:border-gray-600 disabled:opacity-50'
                  } ${selectedMoves.length >= 4 && !selectedMoves.includes(move) ? 'opacity-50 cursor-not-allowed' : ''}`}
                  disabled={selectedMoves.length >= 4 && !selectedMoves.includes(move)}
                >
                  {move}
                </button>
              ))}
            </div>

            {selectedMoves.length > 0 && (
              <div className="mt-6 pt-6 border-t border-white/10">
                <p className="text-[8px] text-yellow-500 uppercase tracking-widest font-bold mb-3">Selected Moves:</p>
                <div className="flex flex-wrap gap-2">
                  {selectedMoves.map(move => (
                    <div key={move} className="bg-yellow-500/20 border border-yellow-500 px-3 py-1 rounded-lg text-[8px] font-retro">
                      {move}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="mt-12 flex flex-col md:flex-row gap-4 justify-center pb-8">
            <Link
              href="/"
              className="px-8 py-4 border-4 border-gray-600 hover:border-gray-500 text-gray-400 hover:text-white font-retro text-[10px] transition-all uppercase tracking-[0.1em]"
            >
              ← BACK
            </Link>
            <button
              className="px-8 py-4 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-retro text-[10px] border-2 md:border-4 border-yellow-600 transition-all shadow-[0_0_30px_rgba(234,179,8,0.2)] hover:shadow-[0_0_40px_rgba(234,179,8,0.4)]"
              style={{ clipPath: 'polygon(15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 15px)' }}
            >
              SAVE & TEST BATTLE
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
