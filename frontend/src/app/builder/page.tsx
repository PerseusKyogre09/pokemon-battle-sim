'use client';
import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  calculateHP,
  calculateOtherStat,
  NATURES,
  TYPE_COLORS,
  StatName,
  getNatureMultiplier,
  exportTeamToShowdown,
  parseShowdownTeam,
  parseShowdownSet
} from '@/lib/pokemon-utils';
import { API_BASE_URL, getAllSets, startBattle, searchPokemon, getPokemonMoves } from '@/lib/api';


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
  legalMoves: string[];
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
  availableMoves: [],
  legalMoves: []
};

const STAT_LABELS: Record<StatName, string> = {
  hp: 'HP', attack: 'Atk', defense: 'Def', spAtk: 'SpA', spDef: 'SpD', speed: 'Spe'
};

const POKEMON_TYPES = Object.keys(TYPE_COLORS);

interface Team {
  id: string;
  name: string;
  members: TeamMember[];
  createdAt: Date;
  updatedAt: Date;
}

export default function PokemonBuilder() {
  const [cookieConsent, setCookieConsent] = useState<boolean | null>(null);
  const [hasLoadedFromCookies, setHasLoadedFromCookies] = useState(false);

  const [teams, setTeams] = useState<Team[]>([
    {
      id: '1',
      name: 'Untitled 1',
      members: [{ ...DEFAULT_MEMBER }],
      createdAt: new Date(),
      updatedAt: new Date(),
    },
  ]);
  const [activeTeamId, setActiveTeamId] = useState('1');
  const [editingMemberIndex, setEditingMemberIndex] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'team-list' | 'team-edit'>('team-list');

  const [modal, setModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: 'alert' | 'confirm' | 'prompt';
    inputValue?: string;
    onConfirm?: (val: any) => void;
    onCancel?: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    type: 'alert'
  });

  const showAlert = (title: string, message: string, onConfirm?: () => void) => {
    setModal({ isOpen: true, title, message, type: 'alert', onConfirm });
  };

  const showConfirm = (title: string, message: string, onConfirm: () => void, onCancel?: () => void) => {
    setModal({ isOpen: true, title, message, type: 'confirm', onConfirm, onCancel });
  };

  const showPrompt = (title: string, message: string, onConfirm: (val: string) => void) => {
    setModal({ isOpen: true, title, message, type: 'prompt', inputValue: '', onConfirm });
  };

  const persistTeamsToLocalStorage = (nextTeams: Team[], activeId: string) => {
    if (cookieConsent !== true) return;

    try {
      const serializedTeams = nextTeams.map(t => ({
        id: t.id,
        name: t.name,
        export: exportTeamToShowdown(t.members),
        createdAt: t.createdAt,
        updatedAt: t.updatedAt
      }));
      localStorage.setItem('pokeLab_teams_v2', JSON.stringify(serializedTeams));
      localStorage.setItem('pokeLab_activeTeamId', activeId);
    } catch (e) {
      console.error('Failed to persist teams to localStorage', e);
    }
  };

  useEffect(() => {
    if (hasLoadedFromCookies) return;
    setHasLoadedFromCookies(true);

    const loadPersistedData = async () => {
      const consentCookie = document.cookie.split('; ').find(row => row.startsWith('pokeLab_consent='));
      if (consentCookie) {
        const consent = consentCookie.split('=')[1] === 'true';
        setCookieConsent(consent);
        
        if (consent) {
          const teamsData = localStorage.getItem('pokeLab_teams_v2');
          const activeId = localStorage.getItem('pokeLab_activeTeamId');

          if (teamsData) {
            try {
              const parsed = JSON.parse(teamsData);
              const loadedTeams = await Promise.all(parsed.map(async (t: any) => {
                const members = await Promise.all(parseShowdownTeam(t.export).map(async (set, idx) => {
                  const fullData = await fetchFullPokemonData(set.species);
                  return {
                    ...DEFAULT_MEMBER,
                    ...fullData,
                    ...set,
                    id: `${t.id}-${idx}`
                  };
                }));

                return {
                  ...t,
                  members: members.length > 0 ? members : [{ ...DEFAULT_MEMBER, id: `${t.id}-1` }],
                  createdAt: new Date(t.createdAt),
                  updatedAt: new Date(t.updatedAt),
                };
              }));

              if (loadedTeams.length > 0) {
                setTeams(loadedTeams);
                if (activeId && loadedTeams.find((t: Team) => t.id === activeId)) {
                  setActiveTeamId(activeId);
                } else {
                  setActiveTeamId(loadedTeams[0].id);
                }
              }
            } catch (e) {
              console.error('Failed to load teams from localStorage', e);
            }
          }
        }
      }
    };

    loadPersistedData();
  }, [hasLoadedFromCookies]);

  useEffect(() => {
    if (hasLoadedFromCookies && cookieConsent === true) {
      persistTeamsToLocalStorage(teams, activeTeamId);
    }
  }, [teams, activeTeamId, hasLoadedFromCookies, cookieConsent]);

  const activeTeam = teams.find(t => t.id === activeTeamId) || teams[0] || {
    id: '1',
    name: 'Untitled 1',
    members: [{ ...DEFAULT_MEMBER }],
    createdAt: new Date(),
    updatedAt: new Date(),
  };
  const team = activeTeam.members?.length ? activeTeam.members : [{ ...DEFAULT_MEMBER }];
  const activeIndex = Math.min(editingMemberIndex ?? 0, Math.max(team.length - 1, 0));
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [allItems, setAllItems] = useState<string[]>([]);
  const [smogonSets, setSmogonSets] = useState<any[]>([]);
  const [allSpecies, setAllSpecies] = useState<any[]>([]);
  const [allMoves, setAllMoves] = useState<string[]>([]);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isVerified, setIsVerified] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  const currentMon = team[activeIndex] || team[0] || { ...DEFAULT_MEMBER };
  const totalEVs = Object.values(currentMon.evs || DEFAULT_MEMBER.evs).reduce((a, b) => a + b, 0);
  const router = useRouter();

  useEffect(() => {
    const fetchCommonData = async () => {
      try {
        const [itemsRes, speciesRes, customItemsRes, movesRes] = await Promise.all([
          fetch('https://pokeapi.co/api/v2/item?limit=2000').then(r => r.json()).catch(() => ({ results: [] })),
          fetch('https://pokeapi.co/api/v2/pokemon-species?limit=1000').then(r => r.json()).catch(() => ({ results: [] })),
          fetch(`${API_BASE_URL}/items`).then(r => r.json()).catch(() => ({ items: [] })),
          fetch(`${API_BASE_URL}/all-moves`).then(r => r.json()).catch(() => ({ success: false, moves: [] }))
        ]);

        const pokeApiItems = (itemsRes.results || []).map((i: any) => i.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()));
        const customItems = customItemsRes.items || [];
        const mergedItems = Array.from(new Set([...pokeApiItems, ...customItems])).sort();

        setAllItems(mergedItems);
        setAllSpecies(speciesRes.results || []);
        if (movesRes.success) {
          setAllMoves(movesRes.moves || []);
        }
      } catch (e) {
        console.error("Failed to fetch common data", e);
      }
    };
    fetchCommonData();
  }, []);

  const fetchFullPokemonData = async (speciesName: string) => {
    if (!speciesName) return null;
    try {
      const res = await fetch(`https://pokeapi.co/api/v2/pokemon/${speciesName.toLowerCase().replace(/ /g, '-')}`);
      if (!res.ok) return null;
      const data = await res.json();
      const backendMoves = await getPokemonMoves(speciesName);

      const stats: Record<StatName, number> = {
        hp: data.stats[0].base_stat,
        attack: data.stats[1].base_stat,
        defense: data.stats[2].base_stat,
        spAtk: data.stats[3].base_stat,
        spDef: data.stats[4].base_stat,
        speed: data.stats[5].base_stat,
      };

      const gen5 = data.sprites.versions?.['generation-v']?.['black-white'];
      let spriteUrl = gen5?.animated?.front_default || gen5?.front_default || data.sprites.front_default || data.sprites.other['official-artwork'].front_default;
      
      if (data.name.toLowerCase().includes('zygarde-mega')) {
        spriteUrl = "https://pbs.twimg.com/media/G3lRUbgXMAA3jdG?format=png&name=small";
      }

      const pokeApiMoves = data.moves.map((m: any) => m.move.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()));
      
      return {
        baseStats: stats,
        types: data.types.map((t: any) => t.type.name),
        sprite: spriteUrl,
        allSprites: data.name.toLowerCase().includes('zygarde-mega') ? null : data.sprites,
        availableAbilities: data.abilities.map((a: any) => a.ability.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())),
        availableMoves: Array.from(new Set([...backendMoves, ...pokeApiMoves])).sort(),
        legalMoves: backendMoves,
      };
    } catch (e) {
      console.error(e);
      return null;
    }
  };

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

  useEffect(() => {
    const refreshMoves = async () => {
      if (!currentMon.species) return;
      
      const moves = await getPokemonMoves(currentMon.species);
      if (moves.length > 0) {
        updateCurrentMon({ 
          legalMoves: moves,
          availableMoves: Array.from(new Set([...currentMon.availableMoves, ...moves])).sort()
        });
      }
    };
    refreshMoves();
  }, [currentMon.species]);

  const handleLaunchBattle = async (teamToLaunch: TeamMember[]) => {
    if (teamToLaunch.length < 6) {
      showConfirm(
        "Incomplete Team",
        `Your team only has ${teamToLaunch.length} Pokémon. Most battles require 6. Continue anyway?`,
        () => executeLaunch(teamToLaunch)
      );
      return;
    }
    executeLaunch(teamToLaunch);
  };

  const executeLaunch = async (teamToLaunch: TeamMember[]) => {
    setIsSearching(true);
    try {
      const formattedTeam = teamToLaunch.map(mon => ({
        name: mon.species.toLowerCase(),
        ability: (mon.ability || '').toLowerCase().replace(/ /g, '-'),
        item: (mon.item || '').toLowerCase().replace(/ /g, '-'),
        moves: mon.moves.filter(m => m && m.trim() !== '').map(m => m.toLowerCase().replace(/ /g, '-')),
        nature: mon.nature,
        evs: mon.evs,
        ivs: mon.ivs,
        shiny: mon.shiny
      }));

      const battleState = await startBattle('', null, 'random', formattedTeam, '6v6');
      localStorage.setItem('initialBattleState', JSON.stringify(battleState));
      router.push('/battle');
    } catch (e) {
      console.error(e);
      showAlert("Launch Failed", "Failed to initialize battle sequence. Ensure your backend is running.");
    } finally {
      setIsSearching(false);
    }
  };

  const renameTeam = (id: string, newName: string) => {
    setTeams(prev => prev.map(t => t.id === id ? { ...t, name: newName, updatedAt: new Date() } : t));
  };

  const updateCurrentMon = (updates: Partial<TeamMember>) => {
    setIsVerified(false);
    setTeams(prev => prev.map(t => {
      if (t.id === activeTeamId) {
        const newMembers = [...t.members];
        newMembers[activeIndex] = { ...newMembers[activeIndex], ...updates };
        return { ...t, members: newMembers, updatedAt: new Date() };
      }
      return t;
    }));
  };

  const addMember = () => {
    if (team.length >= 6) return;
    const newId = Date.now().toString();
    const newMember = { ...DEFAULT_MEMBER, id: newId };
    setTeams(prev => prev.map(t => {
      if (t.id === activeTeamId) {
        return { ...t, members: [...t.members, newMember], updatedAt: new Date() };
      }
      return t;
    }));
    setIsVerified(false);
  };

  const removeMember = (idx: number) => {
    if (team.length <= 1) return;
    setTeams(prev => prev.map(t => {
      if (t.id === activeTeamId) {
        return { ...t, members: t.members.filter((_, i) => i !== idx), updatedAt: new Date() };
      }
      return t;
    }));
    if (editingMemberIndex !== null && editingMemberIndex >= idx && editingMemberIndex > 0) {
      setEditingMemberIndex(prev => (prev ? prev - 1 : 0));
    }
    setIsVerified(false);
  };

  const deleteTeam = (id: string) => {
    if (teams.length <= 1) {
      showAlert("Cannot Delete", "You must have at least one team.");
      return;
    }
    showConfirm(
      "Delete Team",
      "Are you sure you want to delete this team? This action cannot be undone.",
      () => {
        setTeams(prev => {
          const next = prev.filter(t => t.id !== id);
          if (activeTeamId === id) {
            setActiveTeamId(next[0].id);
          }
          return next;
        });
      }
    );
  };

  const clearAllData = () => {
    showConfirm(
      "Clear All Data",
      "WARNING: This will delete ALL teams and reset your browser storage. Please ensure you have EXPORTED your teams first if you wish to keep them. Proceed?",
      () => {
        localStorage.removeItem('pokeLab_teams_v2');
        localStorage.removeItem('pokeLab_activeTeamId');
        document.cookie = 'pokeLab_consent=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
        window.location.reload();
      }
    );
  };

  const addTeam = () => {
    const nextId = Date.now().toString();
    const newTeam: Team = {
      id: nextId,
      name: `Untitled ${teams.length + 1}`,
      members: [{ ...DEFAULT_MEMBER, id: `${nextId}-1` }],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    setTeams(prev => [...prev, newTeam]);
    setActiveTeamId(nextId);
    setEditingMemberIndex(null);
  };

  const ensureMemberSlotAndEdit = (idx: number) => {
    setTeams(prev => prev.map(t => {
      if (t.id === activeTeamId) {
        const newMembers = [...t.members];
        while (newMembers.length <= idx) {
          const newId = Date.now().toString() + '-' + newMembers.length.toString();
          newMembers.push({ ...DEFAULT_MEMBER, id: newId });
        }
        return { ...t, members: newMembers, updatedAt: new Date() };
      }
      return t;
    }));
    setEditingMemberIndex(idx);
  };
  const saveTeamsNow = () => {
    if (cookieConsent === null) {
      showConfirm(
        "Enable Browser Storage",
        "Save teams in your browser? This allows you to keep your teams across sessions.",
        () => {
          setCookieConsent(true);
          document.cookie = `pokeLab_consent=true; path=/; max-age=${60 * 60 * 24 * 365}`;
          persistTeamsToLocalStorage(teams, activeTeamId);
          showAlert("Success", "Teams will now be automatically saved to your browser.");
        }
      );
      return;
    }

    if (cookieConsent === false) {
      showAlert("Storage Disabled", "Local saving is disabled. Accept saving first to store teams.");
      return;
    }

    persistTeamsToLocalStorage(teams, activeTeamId);
    showAlert("Success", "Teams saved to browser storage.");
  };


  const handleSpeciesSearch = async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const data = await searchPokemon(q);
      if (data.success) {
        setSearchResults(data.results);
      }
    } catch (e) {
      console.error("Search failed", e);
    } finally {
      setIsSearching(false);
    }
  };

  const selectSpecies = async (speciesData: any) => {
    const speciesName = speciesData.name;
    try {
      const data = await fetchFullPokemonData(speciesName);
      if (!data) return;

      const displayName = speciesData.display_name || (speciesName.charAt(0).toUpperCase() + speciesName.slice(1));

      updateCurrentMon({
        species: displayName,
        ...data,
        ability: data.availableAbilities[0] || '',
        item: speciesData.item || '',
        moves: speciesData.moveset ? speciesData.moveset.map((m: string) => m.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())) : ['', '', '', ''],
        teraType: data.types[0].charAt(0).toUpperCase() + data.types[0].slice(1)
      });
      setSearchQuery('');
      setSearchResults([]);
    } catch (e) {
      console.error(e);
    }
  };

  const isAbilityValid = currentMon.ability === '' || currentMon.availableAbilities.includes(currentMon.ability);
  const invalidMoves = currentMon.moves.filter(m => m && m.trim() !== '' && !currentMon.legalMoves.includes(m));
  const isItemValid = currentMon.item === '' || allItems.some(item => item.toLowerCase() === currentMon.item.toLowerCase());

  const getValidationErrors = () => {
    const errors: { message: string, fix?: () => void, fixLabel?: string }[] = [];
    if (!currentMon.species) return [{ message: "No species selected" }];

    if (currentMon.species.toLowerCase().includes('zacian-crowned') && currentMon.item.toLowerCase() !== 'rusted sword') {
      errors.push({
        message: "Zacian-Crowned requires Rusted Sword",
        fix: () => updateCurrentMon({ item: 'Rusted Sword' }),
        fixLabel: "Equip Rusted Sword"
      });
    }
    if (currentMon.species.toLowerCase().includes('zamazenta-crowned') && currentMon.item.toLowerCase() !== 'rusted shield') {
      errors.push({
        message: "Zamazenta-Crowned requires Rusted Shield",
        fix: () => updateCurrentMon({ item: 'Rusted Shield' }),
        fixLabel: "Equip Rusted Shield"
      });
    }
    if (currentMon.species.toLowerCase().includes('giratina-origin') && currentMon.item.toLowerCase() !== 'griseous orb') {
      errors.push({
        message: "Giratina-Origin requires Griseous Orb",
        fix: () => updateCurrentMon({ item: 'Griseous Orb' }),
        fixLabel: "Equip Griseous Orb"
      });
    }

    if (invalidMoves.length > 0) {
      errors.push({
        message: `Illegal moves: ${invalidMoves.join(', ')}`,
        fix: () => {
          const newMoves = currentMon.moves.map(m => currentMon.legalMoves.includes(m) ? m : '');
          updateCurrentMon({ moves: newMoves });
        },
        fixLabel: "Remove Illegal Moves"
      });
    }

    if (totalEVs > 510) {
      errors.push({
        message: `Total EVs exceed 510 limit (${totalEVs})`,
        fix: () => {
          const resetEvs = { hp: 0, attack: 0, defense: 0, spAtk: 0, spDef: 0, speed: 0 };
          updateCurrentMon({ evs: resetEvs });
        },
        fixLabel: "Reset EVs"
      });
    }

    return errors;
  };

  const isTeamValid = team.every(mon => mon.species !== '');
  const validationIssues = getValidationErrors();
  const isMonValid = currentMon.species !== '' && validationIssues.length === 0;

  const applySmogonSet = (set: any) => {
    const newEvs = { hp: 0, attack: 0, defense: 0, spAtk: 0, spDef: 0, speed: 0 };
    if (set.evs) {
      Object.entries(set.evs).forEach(([stat, val]) => {
        const key = stat.toLowerCase() as StatName;
        if (key in newEvs) newEvs[key] = val as number;
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


  return (
    <div className="min-h-screen bg-[#020617] text-white font-retro overflow-x-hidden relative selection:bg-yellow-500/30">
      <div className="fixed inset-0 bg-[url('/images/battle-background.jpeg')] bg-cover bg-center opacity-10 blur-md pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-br from-[#020617] via-slate-900/80 to-[#020617] pointer-events-none" />

      <div className="fixed top-[-10%] right-[-10%] w-[50%] h-[50%] bg-yellow-500/10 rounded-full blur-[120px] animate-pulse pointer-events-none" />
      <div className="fixed bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[100px] animate-pulse pointer-events-none" />

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

          {editingMemberIndex !== null && (
            <div className="flex items-center space-x-0.5 bg-black/40 p-1 rounded-xl border border-white/5 overflow-x-auto scrollbar-hide">
                  {team.map((mon, idx) => (
                    <div key={mon.id} className="relative group/tab flex-shrink-0">
                      <button
                        onClick={() => ensureMemberSlotAndEdit(idx)}
                        className={`px-2 sm:px-4 py-2 rounded-lg text-[8px] sm:text-[10px] uppercase tracking-tighter transition-all flex items-center gap-1 sm:gap-2 whitespace-nowrap ${activeIndex === idx
                          ? 'bg-yellow-500 text-slate-900 font-bold shadow-lg shadow-yellow-500/20'
                          : 'hover:bg-white/5 text-gray-400'
                          }`}
                      >
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${activeIndex === idx ? 'bg-slate-900' : 'bg-gray-600'}`} />
                        <span className="truncate max-w-[60px] sm:max-w-full">{mon.species || 'Empty'}</span>
                      </button>
                      {team.length > 1 && (
                        <button
                          onClick={(e) => { e.stopPropagation(); removeMember(idx); }}
                          className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-[8px] flex items-center justify-center opacity-0 group-hover/tab:opacity-100 hover:bg-red-600 transition-all shadow-lg z-10"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
              {team.length < 6 && (
                <button
                  onClick={addMember}
                  className="w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center text-gray-400 hover:text-yellow-500 hover:bg-white/5 rounded-lg transition-all text-lg sm:text-xl flex-shrink-0"
                  title="Add Team Member"
                >
                  +
                </button>
              )}
            </div>
          )}

          <div className="hidden lg:block text-gray-500 text-[9px] uppercase tracking-[0.4em] font-light">
            {editingMemberIndex !== null ? '[ TEAM EDITOR ]' : '[ TEAM MANAGER ]'}
          </div>
        </div>
      </header>

      {editingMemberIndex === null ? (
        <main className={`container mx-auto px-4 py-8 relative z-10 ${cookieConsent === null ? 'pb-48 md:pb-40' : ''}`}>
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              <div className="lg:col-span-1">
                <div className="glass-panel p-6 rounded-none sticky top-20 flex flex-col h-[calc(100vh-120px)]">
                  <div className="flex items-center justify-between gap-3 mb-4">
                    <h2 className="text-yellow-500 font-bold uppercase text-[10px] md:text-[11px] tracking-[0.2em] block">All Teams ({teams.length})</h2>
                    <button
                      onClick={addTeam}
                      className="px-3 py-1.5 rounded-none bg-white/5 border border-white/10 hover:border-yellow-500/40 hover:bg-yellow-500/10 text-[8px] uppercase font-bold tracking-widest text-gray-300 transition-all"
                    >
                      New Team
                    </button>
                  </div>
                  <div className="space-y-2 overflow-y-auto flex-1 pr-1 scrollbar-thin scrollbar-thumb-white/10">
                    {teams.map(t => {
                      const memberCount = t.members.filter(m => m.species !== '').length;
                      return (
                        <div key={t.id} className="relative group">
                          <button
                            onClick={() => setActiveTeamId(t.id)}
                            className={`w-full text-left px-4 py-3 rounded-none border transition-all ${activeTeamId === t.id
                              ? 'bg-yellow-500/20 border-yellow-500/30 shadow-[inset_0_0_20px_rgba(234,179,8,0.05)]'
                              : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                              }`}
                          >
                            <div className="text-[9px] md:text-[10px] font-bold uppercase truncate pr-6">{t.name}</div>
                            <div className="text-[7px] md:text-[8px] text-gray-500 mt-1">{memberCount}/6 Pokémon</div>
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); deleteTeam(t.id); }}
                            className="absolute top-1/2 -translate-y-1/2 right-2 p-2 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                            title="Delete Team"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-6 pt-6 border-t border-white/5">
                    <button
                      onClick={clearAllData}
                      className="w-full py-3 bg-red-500/5 border border-red-500/20 text-red-400/60 hover:text-red-400 hover:bg-red-500/10 hover:border-red-500/40 text-[8px] uppercase font-bold tracking-[0.3em] transition-all rounded-none"
                    >
                      Clear All Data
                    </button>
                  </div>
                </div>
              </div>

              <div className="lg:col-span-3">
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={activeTeam.name}
                      onChange={(e) => renameTeam(activeTeam.id, e.target.value)}
                      className="bg-transparent text-white font-bold uppercase text-[14px] md:text-[18px] tracking-[0.2em] outline-none border-b border-transparent focus:border-yellow-500/50 w-full transition-all"
                      placeholder="Enter Team Name..."
                    />
                    <div className="text-[8px] md:text-[9px] text-gray-500 uppercase tracking-widest mt-1">
                      Updated: {activeTeam.updatedAt.toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        const text = exportTeamToShowdown(team);
                        navigator.clipboard.writeText(text);
                        showAlert("Export Successful", "Team exported to clipboard in Showdown format!");
                      }}
                      className="px-4 py-2 bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[8px] uppercase font-bold rounded-xl hover:bg-blue-500/20 transition-all"
                    >
                      Export
                    </button>
                    <button
                      onClick={() => {
                        showPrompt(
                          "Bulk Import",
                          "Paste your Showdown team here:",
                          async (input) => {
                            if (!input) return;
                            const sets = parseShowdownTeam(input);
                            if (sets.length === 0) {
                              showAlert("Import Failed", "Invalid format! Please paste a valid Showdown export.");
                              return;
                            }
                            const importedMembers = await Promise.all(sets.slice(0, 6).map(async (set, idx) => {
                              const fullData = await fetchFullPokemonData(set.species);
                              return {
                                ...DEFAULT_MEMBER,
                                ...fullData,
                                ...set,
                                id: `${activeTeam.id}-${Date.now()}-${idx}`
                              };
                            }));
                            setTeams(prev => prev.map(t => t.id === activeTeamId ? { ...t, members: importedMembers, updatedAt: new Date() } : t));
                          }
                        );
                      }}
                      className="px-4 py-2 bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 text-[8px] uppercase font-bold rounded-xl hover:bg-yellow-500/20 transition-all"
                    >
                      Import
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[0, 1, 2, 3, 4, 5].map((idx) => {
                    const mon = team[idx];
                    const hasSpecies = mon && mon.species !== '';

                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-2xl border transition-all group cursor-pointer ${hasSpecies
                          ? 'bg-white/5 border-white/10 hover:border-yellow-500/50 hover:bg-yellow-500/5'
                          : 'border-dashed border-white/20 hover:border-white/40 hover:bg-white/5'
                          }`}
                        onClick={() => ensureMemberSlotAndEdit(idx)}
                      >
                        {hasSpecies ? (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2 mb-3">
                              <img
                                src={mon.sprite}
                                alt={mon.species}
                                className="w-12 h-12 object-contain"
                                style={{ imageRendering: 'pixelated' }}
                              />
                              <div className="flex-1 text-left">
                                <div className="text-[10px] font-bold uppercase truncate">{mon.nickname || mon.species}</div>
                                <div className="text-[8px] text-gray-500">{mon.species}</div>
                              </div>
                            </div>
                            <div className="flex gap-1 flex-wrap">
                              {mon.types.slice(0, 2).map(t => (
                                <span
                                  key={t}
                                  className="px-2 py-1 rounded text-[7px] uppercase font-bold"
                                  style={{ backgroundColor: TYPE_COLORS[t] || '#777', color: 'white' }}
                                >
                                  {t}
                                </span>
                              ))}
                            </div>
                            <div className="pt-2 border-t border-white/10 grid grid-cols-3 gap-2 text-center">
                              <div>
                                <div className="text-[7px] text-gray-500 uppercase">Item</div>
                                <div className="text-[8px] font-mono font-bold truncate">{mon.item || '—'}</div>
                              </div>
                              <div>
                                <div className="text-[7px] text-gray-500 uppercase">Ability</div>
                                <div className="text-[8px] font-bold truncate">{mon.ability}</div>
                              </div>
                              <div>
                                <div className="text-[7px] text-gray-500 uppercase">Level</div>
                                <div className="text-[8px] font-bold">{mon.level}</div>
                              </div>
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                ensureMemberSlotAndEdit(idx);
                              }}
                              className="w-full py-2 mt-3 bg-yellow-500/20 hover:bg-yellow-500/40 border border-yellow-500/30 text-yellow-400 text-[8px] uppercase font-bold rounded-lg transition-all"
                            >
                              Edit Pokémon
                            </button>
                          </div>
                        ) : (
                          <div className="h-32 flex items-center justify-center">
                            <div className="text-center">
                              <div className="text-[10px] font-bold uppercase text-gray-500 mb-2">Empty Slot {idx + 1}</div>
                                <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  ensureMemberSlotAndEdit(idx);
                                }}
                                className="text-[8px] text-yellow-400 uppercase font-bold hover:text-yellow-300 transition-colors"
                              >
                                Add Pokémon
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="mt-8 flex gap-4 justify-end">
                  <Link
                    href="/"
                    className="px-6 py-3 glass-panel border border-white/10 hover:border-white/20 rounded-2xl text-[10px] md:text-[11px] uppercase tracking-[0.2em] font-bold text-gray-400 hover:text-white transition-all"
                  >
                    Back to Home
                  </Link>
                  <button
                    onClick={saveTeamsNow}
                    className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/15 hover:border-yellow-500/40 text-white rounded-2xl text-[10px] md:text-[11px] uppercase font-bold tracking-[0.2em] transition-all active:scale-95"
                  >
                    Save Teams
                  </button>
                  <button
                    onClick={() => {
                      const validMembers = team.filter(m => m.species !== '');
                      if (validMembers.length === 0) {
                        showAlert("Empty Roster", "Your team is empty! Add at least one Pokémon.");
                        return;
                      }
                      handleLaunchBattle(validMembers);
                    }}
                    disabled={isSearching}
                    className="px-8 py-3 bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-400 hover:to-amber-500 text-slate-900 rounded-2xl text-[10px] md:text-[11px] uppercase font-bold tracking-[0.2em] shadow-[0_10px_30px_rgba(234,179,8,0.3)] hover:shadow-[0_15px_40px_rgba(234,179,8,0.5)] transition-all active:scale-95 disabled:opacity-50 disabled:grayscale"
                  >
                    {isSearching ? 'Launching...' : 'Launch Battle'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      ) : (
        <main className="container mx-auto px-4 py-8 relative z-10">
        <div className="max-w-7xl mx-auto">

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">

            <div className="lg:col-span-4 space-y-6">
              <div className="glass-panel p-4 md:p-6 rounded-3xl relative z-[100] group">
                <div className="absolute top-0 left-0 w-1 h-full bg-yellow-500 opacity-50" />
                <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-[9px] tracking-[0.2em] block mb-3 md:mb-4">
                  Species Lookup
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleSpeciesSearch(e.target.value)}
                    className="w-full px-3 md:px-4 py-2 md:py-3 builder-input rounded-xl text-[10px] md:text-[11px] placeholder:text-slate-600"
                    placeholder="Search Pokemon..."
                  />
                  {searchResults.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 glass-panel rounded-xl border border-yellow-500/30 overflow-hidden z-[200] shadow-2xl">
                      {searchResults.map((p) => (
                        <button
                          key={p.name}
                          onClick={() => selectSpecies(p)}
                          className="w-full px-4 py-3 text-left hover:bg-yellow-500 hover:text-slate-900 transition-colors text-[10px] uppercase font-bold border-b border-white/5 last:border-0"
                        >
                          {p.display_name || p.name.replace(/-/g, ' ')}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="lg:col-span-8 glass-panel p-4 md:p-8 rounded-3xl grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8 items-center relative overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none select-none p-4 md:p-12 overflow-hidden z-0">
                <h1
                  className="font-black uppercase italic whitespace-nowrap leading-none tracking-tighter text-2xl md:text-6xl"
                >
                  {currentMon.species.length > 10 ? currentMon.species.slice(0, 8) + '...' : currentMon.species}
                </h1>
              </div>

              <div className="flex flex-col items-center justify-center space-y-4 md:space-y-6">
                <div className="relative w-32 h-32 md:w-48 md:h-48 lg:w-64 lg:h-64 flex items-center justify-center">
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

              <div className="space-y-3 md:space-y-5 w-full">
                <div>
                  <label className="text-gray-500 text-[7px] md:text-[8px] uppercase tracking-widest block mb-1.5 md:mb-2">Nickname</label>
                  <input
                    type="text"
                    value={currentMon.nickname}
                    onChange={(e) => updateCurrentMon({ nickname: e.target.value })}
                    className="w-full px-3 md:px-4 py-1.5 md:py-2 bg-white/5 border border-white/10 rounded-lg text-[9px] md:text-[10px] focus:border-yellow-500 outline-none"
                    placeholder={currentMon.species}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2 md:gap-4">
                  <div>
                    <label className="text-gray-500 text-[7px] md:text-[8px] uppercase tracking-widest block mb-1.5 md:mb-2">Level</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={currentMon.level}
                      onChange={(e) => updateCurrentMon({ level: parseInt(e.target.value) || 100 })}
                      className="w-full px-3 md:px-4 py-1.5 md:py-2 bg-white/5 border border-white/10 rounded-lg text-[9px] md:text-[10px] focus:border-yellow-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-gray-500 text-[7px] md:text-[8px] uppercase tracking-widest block mb-1.5 md:mb-2">Tera Type</label>
                    <select
                      value={currentMon.teraType}
                      onChange={(e) => updateCurrentMon({ teraType: e.target.value })}
                      className="w-full px-3 py-1.5 md:py-2 bg-[#1e293b] border border-white/10 rounded-lg text-[9px] md:text-[10px] outline-none"
                    >
                      {POKEMON_TYPES.map(t => (
                        <option key={t} value={t}>{t.toUpperCase()}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2">
                  <div className="flex gap-2 md:gap-3">
                    <button
                      onClick={() => updateCurrentMon({ gender: 'M' })}
                      className={`w-7 md:w-8 h-7 md:h-8 flex items-center justify-center rounded-lg border transition-all text-sm md:text-base ${currentMon.gender === 'M' ? 'bg-blue-500 border-blue-400' : 'bg-white/5 border-white/10 text-gray-500'}`}
                    >
                      ♂
                    </button>
                    <button
                      onClick={() => updateCurrentMon({ gender: 'F' })}
                      className={`w-7 md:w-8 h-7 md:h-8 flex items-center justify-center rounded-lg border transition-all text-sm md:text-base ${currentMon.gender === 'F' ? 'bg-pink-500 border-pink-400' : 'bg-white/5 border-white/10 text-gray-500'}`}
                    >
                      ♀
                    </button>
                  </div>
                  <button
                    onClick={() => updateCurrentMon({ shiny: !currentMon.shiny })}
                    className={`px-2 md:px-4 py-1.5 md:py-2 rounded-lg border transition-all text-[7px] md:text-[9px] uppercase font-bold ${currentMon.shiny ? 'bg-yellow-500 border-yellow-400 text-slate-900' : 'bg-white/5 border-white/10 text-gray-500'}`}
                  >
                    ★ SHINY
                  </button>
                </div>
              </div>
            </div>
          </div>


          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

            <div className="glass-panel p-4 md:p-8 rounded-3xl space-y-4 md:space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-6">
                <div>
                  <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-[9px] tracking-[0.2em] block mb-2 md:mb-3">Ability</label>
                  <select
                    value={currentMon.ability}
                    onChange={(e) => updateCurrentMon({ ability: e.target.value })}
                    className={`w-full px-3 md:px-4 py-1.5 md:py-3 bg-[#1e293b] border rounded-xl text-[9px] md:text-[10px] outline-none transition-all ${isAbilityValid ? 'border-white/10 focus:border-yellow-500' : 'border-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]'}`}
                  >
                    <option value="" disabled>Select Ability...</option>
                    <optgroup label="Species Abilities">
                      {currentMon.availableAbilities.map(a => <option key={`avail-${a}`} value={a}>{a}</option>)}
                    </optgroup>
                  </select>
                  {!isAbilityValid && <p className="text-red-500 text-[7px] mt-1 uppercase tracking-widest animate-pulse">Illegal Ability</p>}
                </div>
                <div>
                  <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-[9px] tracking-[0.2em] block mb-2 md:mb-3">Held Item</label>
                  <input
                    list="items"
                    type="text"
                    value={currentMon.item}
                    onChange={(e) => updateCurrentMon({ item: e.target.value })}
                    className={`w-full px-3 md:px-4 py-1.5 md:py-3 bg-white/5 border rounded-xl text-[9px] md:text-[10px] outline-none transition-all ${isItemValid ? 'border-white/10 focus:border-yellow-500' : 'border-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]'}`}
                    placeholder="Item..."
                  />
                  <datalist id="items">
                    {allItems.slice(0, 3000).map(i => <option key={i} value={i} />)}
                  </datalist>
                  {!isItemValid && <p className="text-red-500 text-[7px] mt-1 uppercase tracking-widest animate-pulse">Invalid Item</p>}
                </div>
              </div>
            </div>

            <div className="glass-panel p-4 md:p-8 rounded-3xl">
              <label className="text-yellow-500 font-bold uppercase text-[8px] md:text-[9px] tracking-[0.2em] block mb-3 md:mb-4">Moveset</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-4">
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
                  {currentMon.availableMoves.map(m => <option key={`avail-${m}`} value={m} />)}
                  {allMoves.map(m => (
                    !currentMon.availableMoves.includes(m) && <option key={`all-${m}`} value={m} />
                  ))}
                </datalist>
              </div>
            </div>
          </div>

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

          <div className="glass-panel p-4 md:p-8 rounded-3xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 md:p-8 flex items-center gap-2 opacity-50">
              <span className="text-[8px] md:text-[10px] text-gray-400 font-bold uppercase tracking-[0.3em]">EV POOL:</span>
              <span className={`text-[12px] md:text-[14px] font-mono font-bold ${totalEVs > 510 ? 'text-red-500' : 'text-green-400'}`}>
                {510 - totalEVs}
              </span>
            </div>

            <div className="mb-6 md:mb-10">
              <p className="text-[7px] md:text-[8px] text-gray-500 uppercase tracking-widest italic">Precision Tuning for Competitive Excellence</p>
            </div>

            <div className="md:hidden space-y-3">
              {(Object.keys(currentMon.baseStats) as StatName[]).map((stat) => {
                const multiplier = getNatureMultiplier(currentMon.nature, stat);
                const isPlus = multiplier > 1;
                const isMinus = multiplier < 1;

                return (
                  <div key={stat} className="bg-white/5 border border-white/10 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-3">
                      <div className={`text-[9px] font-bold uppercase ${isPlus ? 'text-red-400' : isMinus ? 'text-blue-400' : 'text-white'}`}>
                        {STAT_LABELS[stat]} {isPlus ? '↑' : isMinus ? '↓' : ''}
                      </div>
                      <div className="text-[10px] font-mono font-bold text-yellow-500">{finalStats[stat]}</div>
                    </div>
                    
                    <div className="space-y-2 text-[7px] text-gray-500">
                      <div>Base: <span className="text-white font-mono">{currentMon.baseStats[stat]}</span></div>
                      
                      <div>
                        <div className="flex justify-between mb-1">
                          <span>EV: {currentMon.evs[stat]}/252</span>
                        </div>
                        <div className="relative h-1.5 bg-gray-800 rounded-full overflow-visible group">
                          <div
                            className="absolute inset-y-0 left-0 bg-yellow-500/50 rounded-full pointer-events-none"
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
                              updateCurrentMon({ evs: { ...currentMon.evs, [stat]: val } });
                            }}
                            className="relative w-full h-1.5 cursor-pointer stat-slider appearance-none bg-transparent"
                            style={{
                              WebkitAppearance: 'none',
                            }}
                          />
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between mb-1">
                          <span>IV: {currentMon.ivs[stat]}/31</span>
                        </div>
                        <div className="relative h-1.5 bg-gray-800 rounded-full overflow-visible group">
                          <div
                            className="absolute inset-y-0 left-0 bg-blue-500/50 rounded-full pointer-events-none"
                            style={{ width: `${(currentMon.ivs[stat] / 31) * 100}%` }}
                          />
                          <input
                            type="range"
                            min="0"
                            max="31"
                            value={currentMon.ivs[stat]}
                            onChange={(e) => {
                              const val = parseInt(e.target.value);
                              updateCurrentMon({ ivs: { ...currentMon.ivs, [stat]: val } });
                            }}
                            className="relative w-full h-1.5 cursor-pointer stat-slider appearance-none bg-transparent"
                            style={{
                              WebkitAppearance: 'none',
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="hidden md:block max-w-6xl mx-auto">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {(Object.keys(currentMon.baseStats) as StatName[]).map((stat) => {
                  const multiplier = getNatureMultiplier(currentMon.nature, stat);
                  const isPlus = multiplier > 1;
                  const isMinus = multiplier < 1;
                  const statColor = isPlus ? 'from-red-500/20 to-red-900/20' : isMinus ? 'from-blue-500/20 to-blue-900/20' : 'from-white/5 to-white/10';
                  const borderColor = isPlus ? 'border-red-500/30' : isMinus ? 'border-blue-500/30' : 'border-white/10';

                  return (
                    <div key={stat} className={`bg-gradient-to-br ${statColor} border ${borderColor} rounded-xl p-5 backdrop-blur-sm transition-all hover:border-white/20`}>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className={`text-sm font-bold uppercase tracking-wider ${isPlus ? 'text-red-400' : isMinus ? 'text-blue-400' : 'text-white'}`}>
                          {STAT_LABELS[stat]} {isPlus ? '↑' : isMinus ? '↓' : ''}
                        </h3>
                        <div className="text-xl font-bold text-yellow-500 tracking-widest" style={{ fontFamily: 'var(--font-press-start)', letterSpacing: '0.1em' }}>{finalStats[stat]}</div>
                      </div>

                      <div className="space-y-3 text-xs">
                        <div>
                          <label className="text-gray-500 uppercase font-semibold block mb-2">Base Stat</label>
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
                            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-center font-mono text-gray-300 focus:border-white/30 focus:bg-white/10 outline-none transition-all"
                          />
                        </div>

                        <div>
                          <div className="flex items-center justify-between mb-1.5">
                            <label className="text-gray-500 uppercase font-semibold text-[11px]">EV</label>
                            <span className="text-yellow-500 font-mono font-bold text-[10px]">{currentMon.evs[stat]}/252</span>
                          </div>
                          <div className="relative h-2.5 bg-gray-800 rounded-full overflow-visible group">
                            <div
                              className="absolute inset-y-0 left-0 bg-yellow-500/60 rounded-full pointer-events-none"
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
                              className="relative w-full h-2.5 cursor-pointer stat-slider appearance-none bg-transparent align-middle"
                              style={{
                                WebkitAppearance: 'none',
                                verticalAlign: 'middle',
                              }}
                            />
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-between mb-1.5">
                            <label className="text-gray-500 uppercase font-semibold text-[11px]">IV</label>
                            <span className="text-blue-400 font-mono font-bold text-[10px]">{currentMon.ivs[stat]}/31</span>
                          </div>
                          <div className="relative h-2.5 bg-gray-800 rounded-full overflow-visible group">
                            <div
                              className="absolute inset-y-0 left-0 bg-blue-500/60 rounded-full pointer-events-none"
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
                              className="relative w-full h-2.5 cursor-pointer stat-slider appearance-none bg-transparent align-middle"
                              style={{
                                WebkitAppearance: 'none',
                                verticalAlign: 'middle',
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-8 md:mt-12 pt-6 md:pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4 md:gap-6">
              <div className="flex items-center gap-2 md:gap-4 w-full md:w-auto">
                <label className="text-[8px] md:text-[10px] text-gray-500 uppercase font-bold tracking-widest whitespace-nowrap">Nature:</label>
                <select
                  value={currentMon.nature}
                  onChange={(e) => updateCurrentMon({ nature: e.target.value })}
                  className="flex-1 md:flex-none px-3 md:px-4 py-1.5 md:py-2 bg-[#1e293b] border border-white/10 rounded-xl text-[9px] md:text-[10px] outline-none focus:border-yellow-500 appearance-none min-w-[120px] md:min-w-[150px]"
                >
                  {Object.keys(NATURES).map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>

              <div className="text-[7px] md:text-[8px] text-gray-500 uppercase tracking-widest flex flex-col md:flex-row gap-2 md:gap-4 w-full md:w-auto">
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-400" /> Boosted (+10%)</div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-400" /> Hindered (-10%)</div>
              </div>
            </div>
          </div>

          <div className="mt-12 flex flex-col gap-6 justify-center items-center pb-16">

            {(validationIssues.length > 0 && (isVerified || isValidating)) && (
              <div className="w-full max-w-2xl glass-panel border border-red-500/30 p-6 rounded-3xl animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center gap-3 mb-4 text-red-400">
                  <span className="text-[12px] font-bold uppercase tracking-[0.2em]">Build Discrepancies Detected</span>
                </div>
                <div className="space-y-3">
                  {validationIssues.map((issue, i) => (
                    <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5 gap-3">
                      <p className="text-gray-300 text-[10px] uppercase font-medium tracking-wide">
                        <span className="text-red-500 mr-2">●</span> {issue.message}
                      </p>
                      {issue.fix && (
                        <button
                          onClick={issue.fix}
                          className="px-4 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-400 text-[8px] uppercase font-bold rounded-lg transition-all"
                        >
                          {issue.fixLabel || 'Quick Fix'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {isVerified && validationIssues.length === 0 && (
              <div className="w-full max-w-md bg-green-500/10 border border-green-500/30 p-4 rounded-2xl animate-in zoom-in-95 duration-300 text-center">
                <p className="text-green-400 text-[10px] uppercase font-bold tracking-[0.3em]">✓ Build Verified & Simulation Ready</p>
              </div>
            )}

            <div className="flex flex-col md:flex-row gap-4 md:gap-6 justify-center items-center w-full md:w-auto">
              <Link
                href="/"
                className="px-6 md:px-10 py-3 md:py-4 glass-panel border border-white/10 hover:border-white/20 rounded-2xl text-[10px] md:text-[11px] uppercase tracking-[0.2em] font-bold text-gray-400 hover:text-white transition-all active:scale-95 w-full md:w-auto text-center"
              >
                Discard Project
              </Link>

              <button
                onClick={async () => {
saveTeamsNow();
                  setEditingMemberIndex(null);
                }}
                className="px-6 md:px-10 py-3 md:py-4 bg-white text-slate-900 hover:bg-gray-100 rounded-2xl text-[10px] md:text-[11px] uppercase tracking-[0.2em] font-bold transition-all active:scale-95 w-full md:w-auto"
              >
                Save Pokémon
              </button>

              <div className="relative group w-full md:w-auto">
                {!isVerified ? (
                  <button
                    onClick={async () => {
                      setIsValidating(true);
                      await new Promise(r => setTimeout(r, 800));
                      setIsValidating(false);
                      setIsVerified(true);
                    }}
                    disabled={isValidating}
                    className={`px-8 md:px-12 py-3 md:py-5 bg-white/5 hover:bg-white/10 border border-white/20 hover:border-blue-500/50 text-white rounded-2xl text-[10px] md:text-[12px] uppercase font-bold tracking-[0.2em] transition-all active:scale-95 flex items-center justify-center gap-2 md:gap-3 w-full ${isValidating ? 'cursor-wait opacity-70' : ''}`}
                  >
                    {isValidating ? (
                      <>
                        <div className="w-3 md:w-4 h-3 md:h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        <span className="hidden sm:inline">Scanning Build...</span>
                        <span className="sm:hidden">Scanning...</span>
                      </>
                    ) : (
                      <>
                        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                        Verify
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      const validMembers = team.filter(m => m.species !== '');
                      handleLaunchBattle(validMembers);
                    }}
                    disabled={isSearching || !isMonValid}
                    className={`px-8 md:px-12 py-3 md:py-5 bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-400 hover:to-amber-500 text-slate-900 rounded-2xl text-[10px] md:text-[12px] uppercase font-bold tracking-[0.2em] shadow-[0_10px_30px_rgba(234,179,8,0.3)] hover:shadow-[0_15px_40px_rgba(234,179,8,0.5)] transition-all active:scale-95 group w-full ${isSearching || !isMonValid ? 'opacity-50 cursor-not-allowed grayscale' : ''}`}
                  >
                    {isSearching ? 'SYNCING DATA...' : 'Initialize Battle'} <span className="ml-2 group-hover:translate-x-1 transition-transform inline-block">→</span>
                  </button>
                )}
              </div>
            </div>
          </div>

        </div>
      </main>
      )}

      {modal.isOpen && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-[#020617]/80 backdrop-blur-md animate-in fade-in duration-300" onClick={() => setModal(prev => ({ ...prev, isOpen: false }))} />
          <div className="relative w-full max-w-md bg-slate-900 border border-white/10 rounded-none p-8 shadow-2xl animate-in zoom-in-95 slide-in-from-bottom-8 duration-300">
            <div className="absolute top-0 left-0 w-1 h-full bg-yellow-500" />
            
            <h3 className="text-yellow-500 font-bold uppercase text-[12px] tracking-[0.3em] mb-4">
              {modal.title}
            </h3>
            <p className="text-gray-300 text-[11px] leading-relaxed mb-8 uppercase tracking-wide">
              {modal.message}
            </p>

            {modal.type === 'prompt' && (
              <textarea
                autoFocus
                value={modal.inputValue}
                onChange={(e) => setModal(prev => ({ ...prev, inputValue: e.target.value }))}
                className="w-full h-48 px-4 py-4 bg-black/40 border border-white/10 rounded-none text-[10px] text-white outline-none focus:border-yellow-500 mb-8 font-mono resize-none"
                placeholder="Paste data here..."
              />
            )}

            <div className="flex gap-4 justify-end">
              {modal.type !== 'alert' && (
                <button
                  onClick={() => {
                    setModal(prev => ({ ...prev, isOpen: false }));
                    if (modal.onCancel) modal.onCancel();
                  }}
                  className="px-6 py-2 rounded-none text-[9px] uppercase font-bold tracking-widest text-gray-500 hover:text-white transition-all border border-transparent hover:border-white/10"
                >
                  Cancel
                </button>
              )}
              <button
                onClick={() => {
                  setModal(prev => ({ ...prev, isOpen: false }));
                  if (modal.onConfirm) modal.onConfirm(modal.inputValue);
                }}
                className="px-8 py-2 bg-yellow-500 text-slate-900 rounded-none text-[9px] uppercase font-bold tracking-widest hover:bg-yellow-400 transition-all shadow-lg shadow-yellow-500/20"
              >
                {modal.type === 'confirm' ? 'Confirm' : modal.type === 'prompt' ? 'Import' : 'OK'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="fixed bottom-4 left-4 text-[7px] text-gray-600 font-mono tracking-widest select-none pointer-events-none uppercase">
        System: Online | Latency: 24ms | Session: {Math.random().toString(36).substring(7).toUpperCase()}
      </div>

      {cookieConsent === null && (
        <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-t border-white/10 backdrop-blur-xl p-4 md:p-6 z-[200]">
          <div className="container mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex-1">
              <p className="text-[9px] md:text-[10px] text-gray-300 uppercase tracking-widest font-bold mb-2">
                🍪 Save Your Teams
              </p>
              <p className="text-[8px] text-gray-500 leading-relaxed max-w-2xl">
                We'd like to save your Pokémon teams in your browser using cookies. This helps you keep your teams across sessions without an account.
              </p>
            </div>
            <div className="flex gap-3 w-full md:w-auto">
              <button
                onClick={() => {
                  setCookieConsent(false);
                  document.cookie = 'pokeLab_consent=false; path=/; max-age=' + (60 * 60 * 24 * 365);
                }}
                className="flex-1 md:flex-none px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/20 text-[9px] uppercase font-bold tracking-widest text-gray-300 rounded-lg transition-all"
              >
                Decline
              </button>
              <button
                onClick={() => {
                  setCookieConsent(true);
                  document.cookie = 'pokeLab_consent=true; path=/; max-age=' + (60 * 60 * 24 * 365);
                }}
                className="flex-1 md:flex-none px-6 py-2 bg-yellow-500 hover:bg-yellow-400 text-slate-900 text-[9px] uppercase font-bold tracking-widest rounded-lg transition-all"
              >
                Accept & Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
