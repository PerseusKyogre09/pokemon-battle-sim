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
