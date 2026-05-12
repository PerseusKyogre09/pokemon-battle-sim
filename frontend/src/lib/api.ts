export const resolveApiBaseUrl = () => {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL;
  if (configuredUrl) return configuredUrl.replace(/\/$/, '');

  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:7860/api';
  }

  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api`;
  }

  return '/api';
};

const _rawApiBase = resolveApiBaseUrl();

export const API_BASE_URL = (() => {
  // Log the resolved value at runtime so we can diagnose production behavior
  if (typeof window !== 'undefined') {
    // eslint-disable-next-line no-console
    console.log('API_BASE_URL=', _rawApiBase);
  }

  // Safety: in production, avoid using insecure http:// values. Prefer HTTPS.
  if (process.env.NODE_ENV === 'production' && _rawApiBase.startsWith('http://')) {
    // eslint-disable-next-line no-console
    console.warn('Upgrading insecure API_BASE_URL to https:// in production:', _rawApiBase);
    return _rawApiBase.replace(/^http:\/\//, 'https://');
  }

  return _rawApiBase;
})();

export interface PokemonMove {
  name: string;
  power: number;
  type: string;
  pp: number;
  max_pp: number;
}

export interface StatusEffect {
  type: string;
  name: string;
  is_major: boolean;
  duration: number;
  counter: number;
}

export interface PokemonData {
  name: string;
  current_hp: number;
  max_hp: number;
  sprite: string;
  cry_url?: string;
  types: string[];
  level: number;
  status_effects?: StatusEffect[];
  substitute_hp?: number;
}

export interface BattleState {
  player_pokemon: PokemonData;
  opponent_pokemon: PokemonData;
  player_team?: PokemonData[];
  opponent_team?: PokemonData[];
  player_moves: PokemonMove[];
  start_events?: any[];
  weather?: string;
}

export interface TurnResult {
  player_hp: number;
  opponent_hp: number;
  player_max_hp: number;
  opponent_max_hp: number;
  player_status_effects: StatusEffect[];
  opponent_status_effects: StatusEffect[];
  turn_info: {
    player_first: boolean;
    player_move: string;
    opponent_move: string;
    player_damage: number;
    opponent_damage: number;
    battle_events: any[];
    weather?: string;
  };
  pending_player_switch?: boolean;
  is_game_over: boolean;
  battle_result: string | null;
}

const safeJson = async (response: Response) => {
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch (e) {
      console.error('Failed to parse JSON:', e);
      return { success: false, error: 'Invalid JSON response' };
    }
  }
  return { success: false, error: `Unexpected content type: ${contentType}` };
};

export const searchPokemon = async (query: string, setsOnly: boolean = false) => {
  try {
    const response = await fetch(`${API_BASE_URL}/search-pokemon?q=${query}${setsOnly ? '&sets_only=true' : ''}`);
    const data = await safeJson(response);
    
    if (Array.isArray(data)) {
      return { success: data.length > 0, results: data };
    }
    return {
      success: data.success || false,
      results: data.results || []
    };
  } catch (e) {
    return { success: false, results: [] };
  }
};

export const getMoveset = async (pokemonName: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/get_moveset/${pokemonName}`);
    return await safeJson(response);
  } catch (e) {
    return { success: false, error: 'Network error' };
  }
};

export const getPokemonMoves = async (pokemonName: string): Promise<string[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/pokemon/${pokemonName}/moves`);
    return await safeJson(response);
  } catch (e) {
    console.error("Error fetching pokemon moves:", e);
    return [];
  }
};

export const getAllSets = async (pokemonName: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/get_all_sets/${pokemonName}`);
    return await safeJson(response);
  } catch (e) {
    return { success: false, error: 'Network error' };
  }
};

export const startBattle = async (pokemonName: string, selectedSet?: any, opponentName: string = 'charizard', team?: any, mode?: string): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        pokemon: pokemonName, 
        selected_set: selectedSet,
        opponent: opponentName,
        team: team,
        mode: mode || (team && team.length > 1 ? '6v6' : '1v1')
      }),
    });
    return await safeJson(response);
  } catch (e) {
    return { success: false, error: 'Network error' };
  }
};

export const executeMove = async (moveName?: string, switchIndex?: number, mega?: boolean): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ move: moveName, switch_index: switchIndex, mega: mega }),
    });
    return await safeJson(response);
  } catch (e) {
    return { success: false, error: 'Network error' };
  }
};

// ===== FORM VALIDATION API FUNCTIONS =====

export interface PokemonFormInfo {
  success: boolean;
  species: string;
  legal_forms: string[];
  default_form: string;
  all_forms: Record<string, any>;
  error?: string;
}

export const getPokemonForms = async (species: string): Promise<PokemonFormInfo> => {
  try {
    const response = await fetch(`${API_BASE_URL}/pokemon/${species}/forms`);
    return await safeJson(response);
  } catch (e) {
    return { success: false, species, legal_forms: [''], default_form: '', all_forms: {} };
  }
};

export interface TeamValidationResult {
  valid: boolean;
  errors: Array<{ pokemon_index: number; pokemon_name: string; message: string }>;
  warnings: Array<{ pokemon_index: number; pokemon_name: string; message: string }>;
  team_issues: Array<{ pokemon_index: number; pokemon_name: string; suggested_item: string }>;
  success?: boolean;
  error?: string;
}

export const validateTeam = async (team: Array<{ name: string; item?: string }>): Promise<TeamValidationResult> => {
  try {
    const response = await fetch(`${API_BASE_URL}/validate-team`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team }),
    });
    return await safeJson(response);
  } catch (e) {
    return { 
      valid: false, 
      errors: [], 
      warnings: [], 
      team_issues: [] 
    };
  }
};
