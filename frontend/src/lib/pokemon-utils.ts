export type StatName = 'hp' | 'attack' | 'defense' | 'spAtk' | 'spDef' | 'speed';

export const NATURES: Record<string, { plus?: StatName; minus?: StatName }> = {
  Adamant: { plus: 'attack', minus: 'spAtk' },
  Bashful: {},
  Bold: { plus: 'defense', minus: 'attack' },
  Brave: { plus: 'attack', minus: 'speed' },
  Calm: { plus: 'spDef', minus: 'attack' },
  Careful: { plus: 'spDef', minus: 'spAtk' },
  Docile: {},
  Gentle: { plus: 'spDef', minus: 'defense' },
  Hardy: {},
  Hasty: { plus: 'speed', minus: 'defense' },
  Impish: { plus: 'defense', minus: 'spAtk' },
  Jolly: { plus: 'speed', minus: 'spAtk' },
  Lax: { plus: 'defense', minus: 'spDef' },
  Lonely: { plus: 'attack', minus: 'defense' },
  Mild: { plus: 'spAtk', minus: 'defense' },
  Modest: { plus: 'spAtk', minus: 'attack' },
  Naive: { plus: 'speed', minus: 'spDef' },
  Naughty: { plus: 'attack', minus: 'spDef' },
  Quiet: { plus: 'spAtk', minus: 'speed' },
  Quirky: {},
  Rash: { plus: 'spAtk', minus: 'spDef' },
  Relaxed: { plus: 'defense', minus: 'speed' },
  Sassy: { plus: 'spDef', minus: 'speed' },
  Serious: {},
  Timid: { plus: 'speed', minus: 'attack' },
};

export const calculateHP = (base: number, iv: number, ev: number, level: number, name: string = '') => {
  if (name.toLowerCase() === 'shedinja') return 1;
  return Math.floor(((2 * base + iv + Math.floor(ev / 4)) * level) / 100) + level + 10;
};

export const calculateOtherStat = (
  base: number,
  iv: number,
  ev: number,
  level: number,
  nature: string,
  statName: StatName
) => {
  const baseVal = Math.floor(((2 * base + iv + Math.floor(ev / 4)) * level) / 100) + 5;
  const natureInfo = NATURES[nature] || {};
  let multiplier = 1;
  if (natureInfo.plus === statName) multiplier = 1.1;
  if (natureInfo.minus === statName) multiplier = 0.9;
  return Math.floor(baseVal * multiplier);
};

export const getNatureMultiplier = (nature: string, statName: StatName): number => {
  const natureInfo = NATURES[nature] || {};
  if (natureInfo.plus === statName) return 1.1;
  if (natureInfo.minus === statName) return 0.9;
  return 1;
};

export const TYPE_COLORS: Record<string, string> = {
  normal: '#A8A77A',
  fire: '#EE8130',
  water: '#6390F0',
  electric: '#F7D02C',
  grass: '#7AC74C',
  ice: '#96D9D6',
  fighting: '#C22E28',
  poison: '#A33EA1',
  ground: '#E2BF65',
  flying: '#A98FF3',
  psychic: '#F95587',
  bug: '#A6B91A',
  rock: '#B6A136',
  ghost: '#735797',
  dragon: '#6F35FC',
  dark: '#705746',
  steel: '#B7B7CE',
  fairy: '#D685AD',
};

const SHOWDOWN_STAT_MAP: Record<string, string> = {
  hp: 'HP',
  attack: 'Atk',
  defense: 'Def',
  spAtk: 'SpA',
  spDef: 'SpD',
  speed: 'Spe',
};

const INV_SHOWDOWN_STAT_MAP: Record<string, StatName> = {
  'HP': 'hp',
  'Atk': 'attack',
  'Def': 'defense',
  'SpA': 'spAtk',
  'SpD': 'spDef',
  'Spe': 'speed',
};

export const exportTeamToShowdown = (members: any[]): string => {
  return members
    .filter(mon => mon.species)
    .map(mon => {
      let res = `${mon.nickname && mon.nickname !== mon.species ? `${mon.nickname} (${mon.species})` : mon.species}`;
      if (mon.item) res += ` @ ${mon.item}`;
      res += '\n';
      if (mon.ability) res += `Ability: ${mon.ability}\n`;
      if (mon.level && mon.level !== 100) res += `Level: ${mon.level}\n`;
      if (mon.shiny) res += `Shiny: Yes\n`;
      if (mon.teraType) res += `Tera Type: ${mon.teraType}\n`;
      
      const evs = Object.entries(mon.evs || {}).filter(([_, v]) => (v as number) > 0);
      if (evs.length > 0) {
        res += `EVs: ${evs.map(([s, v]) => `${v} ${SHOWDOWN_STAT_MAP[s]}`).join(' / ')}\n`;
      }
      
      res += `${mon.nature || 'Serious'} Nature\n`;
      
      const ivs = Object.entries(mon.ivs || {}).filter(([_, v]) => (v as number) < 31);
      if (ivs.length > 0) {
        res += `IVs: ${ivs.map(([s, v]) => `${v} ${SHOWDOWN_STAT_MAP[s]}`).join(' / ')}\n`;
      }
      
      (mon.moves || []).filter((m: string) => m && m.trim() !== '').forEach((m: string) => {
        res += `- ${m}\n`;
      });
      
      return res;
    }).join('\n');
};

export const parseShowdownSet = (text: string) => {
  const lines = text.trim().split('\n');
  if (lines.length === 0) return null;

  const set: any = {
    species: '',
    nickname: '',
    item: '',
    ability: '',
    level: 100,
    shiny: false,
    teraType: '',
    nature: 'Serious',
    evs: { hp: 0, attack: 0, defense: 0, spAtk: 0, spDef: 0, speed: 0 },
    ivs: { hp: 31, attack: 31, defense: 31, spAtk: 31, spDef: 31, speed: 31 },
    moves: []
  };

  const firstLine = lines[0].split('@');
  let speciesPart = firstLine[0].trim();
  if (firstLine[1]) set.item = firstLine[1].trim();

  if (speciesPart.includes('(') && speciesPart.includes(')')) {
    const match = speciesPart.match(/(.*) \((.*)\)/);
    if (match) {
      set.nickname = match[1].trim();
      set.species = match[2].trim();
    }
  } else {
    set.species = speciesPart;
  }

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('Ability:')) set.ability = line.replace('Ability:', '').trim();
    else if (line.startsWith('Level:')) set.level = parseInt(line.replace('Level:', '').trim());
    else if (line.startsWith('Shiny:')) set.shiny = line.includes('Yes');
    else if (line.startsWith('Tera Type:')) set.teraType = line.replace('Tera Type:', '').trim();
    else if (line.startsWith('EVs:')) {
      const parts = line.replace('EVs:', '').split('/');
      parts.forEach(p => {
        const [val, stat] = p.trim().split(' ');
        const internalStat = INV_SHOWDOWN_STAT_MAP[stat];
        if (internalStat) set.evs[internalStat] = parseInt(val);
      });
    }
    else if (line.endsWith('Nature')) {
      set.nature = line.replace('Nature', '').trim();
    }
    else if (line.startsWith('IVs:')) {
      const parts = line.replace('IVs:', '').split('/');
      parts.forEach(p => {
        const [val, stat] = p.trim().split(' ');
        const internalStat = INV_SHOWDOWN_STAT_MAP[stat];
        if (internalStat) set.ivs[internalStat] = parseInt(val);
      });
    }
    else if (line.startsWith('-')) {
      set.moves.push(line.replace('-', '').trim());
    }
  }

  while (set.moves.length < 4) set.moves.push('');
  return set;
};

export const parseShowdownTeam = (text: string) => {
  const blocks = text.trim().split(/\n\s*\n/);
  return blocks
    .map(b => parseShowdownSet(b))
    .filter(s => s !== null && s.species && s.species.trim() !== '');
};
