document.addEventListener('DOMContentLoaded', function() {
    const pokemonInput = document.getElementById('pokemon-search');
    const suggestionsDiv = document.getElementById('suggestions');
    const form = document.getElementById('pokemon-form');
    const selectedPokemonDiv = document.getElementById('selected-pokemon');
    const selectedSprite = document.getElementById('selected-sprite');
    const selectedName = document.getElementById('selected-name');
    const selectedTypes = document.getElementById('selected-types');
    const pokedexEntry = document.getElementById('pokedex-entry');
    const statsContainer = document.getElementById('stats-container');
    const movesContainer = document.getElementById('moves-container');
    const pokemonId = document.getElementById('pokemon-id');
    const startBattleButton = document.getElementById('start-battle');
    const setSelection = document.getElementById('set-selection');
    const prevSetButton = document.getElementById('prev-set');
    const nextSetButton = document.getElementById('next-set');
    const setCounter = document.getElementById('set-counter');
    const setInfo = document.getElementById('set-info');
    
    let selectedPokemon = null;
    let availableSets = [];
    let currentSetIndex = 0;
    
    // Debounce function to limit API calls
    function debounce(func, delay) {
        let timeoutId;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(context, args), delay);
        };
    }
    
    // Fetch Pokémon suggestions from PokeAPI
    const fetchPokemonSuggestions = debounce(async (query) => {
        if (!query) {
            suggestionsDiv.classList.add('hidden');
            return;
        }
        
        try {
            const response = await fetch(`https://pokeapi.co/api/v2/pokemon?limit=1000`);
            if (response.ok) {
                const data = await response.json();
                const matches = data.results.filter(pokemon => 
                    pokemon.name.includes(query.toLowerCase())
                );
                
                if (matches.length > 0) {
                    showSuggestions(matches);
                } else {
                    suggestionsDiv.classList.add('hidden');
                }
            }
        } catch (error) {
            console.error('Error searching Pokémon:', error);
            suggestionsDiv.classList.add('hidden');
        }
    }, 300);
    
    // Show suggestions in the dropdown
    function showSuggestions(pokemonList) {
        suggestionsDiv.innerHTML = '';
        pokemonList.slice(0, 5).forEach(pokemon => {
            const div = document.createElement('div');
            div.className = 'px-4 py-2 hover:bg-gray-700 cursor-pointer';
            div.textContent = pokemon.name.charAt(0).toUpperCase() + pokemon.name.slice(1);
            div.addEventListener('click', () => {
                fetchPokemonDetails(pokemon.name);
                suggestionsDiv.classList.add('hidden');
                pokemonInput.value = pokemon.name;
            });
            suggestionsDiv.appendChild(div);
        });
        suggestionsDiv.classList.remove('hidden');
    }
    
    // Fetch and show selected Pokémon details
    async function fetchPokemonDetails(name) {
        try {
            const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${name.toLowerCase()}`);
            if (response.ok) {
                const data = await response.json();
                showSelectedPokemon(data);
            }
        } catch (error) {
            console.error('Error fetching Pokémon details:', error);
        }
    }
    
    // Fetch species data for Pokedex entry
    async function fetchPokemonSpecies(id) {
        try {
            const response = await fetch(`https://pokeapi.co/api/v2/pokemon-species/${id}/`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error fetching Pokémon species:', error);
        }
        return null;
    }
    
    // Format Pokedex entry text
    function formatPokedexEntry(entry) {
        return entry
            .replace(/\f/g, ' ')
            .replace(/\n/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }
    
    // Get English Pokedex entry
    function getEnglishEntry(entries) {
        const entry = entries.find(e => e.language.name === 'en');
        return entry ? formatPokedexEntry(entry.flavor_text) : 'NO POKÉDEX ENTRY AVAILABLE.';
    }
    
    // Format stat name
    function formatStatName(statName) {
        return statName
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    // Calculate color based on stat value
    function getStatColor(value) {
        if (value >= 100) return '#4CAF50';
        if (value >= 80) return '#8BC34A';
        if (value >= 60) return '#FFC107';
        if (value >= 40) return '#FF9800';
        return '#F44336';
    }
    
    // Fetch all available sets for a Pokémon
    async function fetchPokemonSets(pokemonName) {
        try {
            const response = await fetch(`/get_all_sets/${pokemonName.toLowerCase()}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.sets && data.sets.length > 0) {
                    return data.sets;
                }
            }
            
            // Fallback to basic moveset if no sets found
            const fallbackResponse = await fetch(`/get_moveset/${pokemonName.toLowerCase()}`);
            if (fallbackResponse.ok) {
                const fallbackData = await fallbackResponse.json();
                if (fallbackData.moves && fallbackData.moves.length > 0) {
                    return [{
                        format: 'fallback',
                        set_name: 'Default Set',
                        moves: fallbackData.moves,
                        item: '',
                        ability: '',
                        nature: '',
                        evs: {}
                    }];
                }
            }
            
            // Final fallback
            return [{
                format: 'fallback',
                set_name: 'Basic Set',
                moves: ['Tackle', 'Growl', 'Scratch', 'Leer'],
                item: '',
                ability: '',
                nature: '',
                evs: {}
            }];
            
        } catch (error) {
            console.error('Error fetching Pokémon sets:', error);
            return [{
                format: 'fallback',
                set_name: 'Basic Set',
                moves: ['Tackle', 'Growl', 'Scratch', 'Leer'],
                item: '',
                ability: '',
                nature: '',
                evs: {}
            }];
        }
    }

    // Fetch moves for a Pokémon (legacy function for backward compatibility)
    async function fetchPokemonMoves(pokemonName) {
        try {
            // First try to get moves from the local moveset data
            const response = await fetch(`/get_moveset/${pokemonName.toLowerCase()}`);
            if (response.ok) {
                const data = await response.json();
                if (data.moves && data.moves.length > 0) {
                    return data.moves;
                }
            }
            
            // Fallback to PokeAPI if local data not available
            const pokeApiResponse = await fetch(`https://pokeapi.co/api/v2/pokemon/${pokemonName.toLowerCase()}`);
            if (pokeApiResponse.ok) {
                const pokemonData = await pokeApiResponse.json();
                if (pokemonData.moves && pokemonData.moves.length > 0) {
                    // Get up to 4 moves, prioritizing level-up moves
                    const levelUpMoves = pokemonData.moves
                        .filter(move => move.version_group_details.some(detail => 
                            detail.move_learn_method.name === 'level-up' && detail.level_learned_at > 0
                        ))
                        .sort((a, b) => {
                            const aLevel = Math.min(...a.version_group_details
                                .filter(d => d.move_learn_method.name === 'level-up')
                                .map(d => d.level_learned_at));
                            const bLevel = Math.min(...b.version_group_details
                                .filter(d => d.move_learn_method.name === 'level-up')
                                .map(d => d.level_learned_at));
                            return bLevel - aLevel; // Sort by level in descending order
                        });
                    
                    // Get up to 4 moves, starting with level-up moves, then fill with other moves if needed
                    const moves = [
                        ...levelUpMoves.slice(0, 4).map(m => m.move.name.replace('-', ' ')),
                        ...pokemonData.moves
                            .filter(move => !levelUpMoves.includes(move))
                            .slice(0, 4 - Math.min(4, levelUpMoves.length))
                            .map(m => m.move.name.replace('-', ' '))
                    ];
                    
                    return moves.slice(0, 4);
                }
            }
            
            // Default moves if none found
            return ['Tackle', 'Growl', 'Scratch', 'Leer'].slice(0, 4);
            
        } catch (error) {
            console.error('Error fetching Pokémon moves:', error);
            return ['Tackle', 'Growl', 'Scratch', 'Leer'].slice(0, 4);
        }
    }
    
    // Update set selection UI
    function updateSetSelection() {
        if (availableSets.length <= 1) {
            setSelection.classList.add('hidden');
            return;
        }
        
        setSelection.classList.remove('hidden');
        setCounter.textContent = `${currentSetIndex + 1} / ${availableSets.length}`;
        
        // Update navigation buttons
        prevSetButton.disabled = currentSetIndex === 0;
        nextSetButton.disabled = currentSetIndex === availableSets.length - 1;
        
        // Update set info
        const currentSet = availableSets[currentSetIndex];
        let setInfoText = `${currentSet.set_name}`;
        if (currentSet.format !== 'fallback') {
            setInfoText += ` (${currentSet.format})`;
        }
        if (currentSet.item) {
            setInfoText += ` • ${currentSet.item}`;
        }
        if (currentSet.ability) {
            setInfoText += ` • ${currentSet.ability}`;
        }
        if (currentSet.nature) {
            setInfoText += ` • ${currentSet.nature}`;
        }
        setInfo.textContent = setInfoText;
        
        // Update moves display
        updateMovesDisplay();
    }
    
    // Update moves display based on current set
    function updateMovesDisplay() {
        movesContainer.innerHTML = '';
        const currentSet = availableSets[currentSetIndex];
        currentSet.moves.forEach(move => {
            const moveElement = document.createElement('div');
            moveElement.className = 'bg-gray-700 px-3 py-1 rounded text-sm text-center';
            moveElement.textContent = move.charAt(0).toUpperCase() + move.slice(1);
            movesContainer.appendChild(moveElement);
        });
    }
    
    // Show selected Pokemon
    async function showSelectedPokemon(pokemon) {
        selectedPokemon = pokemon;
        
        // Update basic info
        selectedSprite.src = pokemon.sprites.other['official-artwork'].front_default || 
                            pokemon.sprites.front_default;
        selectedName.textContent = pokemon.name.charAt(0).toUpperCase() + pokemon.name.slice(1);
        pokemonId.textContent = `#${String(pokemon.id).padStart(3, '0')}`;
        
        // Update types
        selectedTypes.innerHTML = '';
        pokemon.types.forEach(typeInfo => {
            const type = typeInfo.type.name;
            const typeBadge = document.createElement('span');
            typeBadge.className = `type-badge type-${type} inline-block`;
            typeBadge.textContent = type.toUpperCase();
            selectedTypes.appendChild(typeBadge);
        });
        
        // Show loading states
        pokedexEntry.textContent = 'LOADING...';
        statsContainer.innerHTML = '<div class="text-center py-4">LOADING STATS...</div>';
        movesContainer.innerHTML = '<div class="text-center py-2">LOADING MOVES...</div>';
        
        try {
            // Fetch additional data in parallel
            const [speciesData, sets] = await Promise.all([
                fetchPokemonSpecies(pokemon.id),
                fetchPokemonSets(pokemon.name)
            ]);
            
            // Update Pokedex entry
            const entry = getEnglishEntry(speciesData.flavor_text_entries);
            pokedexEntry.textContent = entry || 'NO POKÉDEX ENTRY AVAILABLE.';
            
            // Update stats
            statsContainer.innerHTML = '';
            pokemon.stats.forEach(statInfo => {
                const statName = statInfo.stat.name;
                const baseStat = statInfo.base_stat;
                
                const statItem = document.createElement('div');
                statItem.className = 'stat-item mb-2';
                statItem.innerHTML = `
                    <div class="flex justify-between mb-1">
                        <span class="text-sm">${formatStatName(statName)}</span>
                        <span class="font-mono">${baseStat}</span>
                    </div>
                    <div class="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div class="h-full" style="width: ${Math.min(100, (baseStat / 255) * 100)}%; background: ${getStatColor(baseStat)};"></div>
                    </div>
                `;
                statsContainer.appendChild(statItem);
            });
            
            // Update sets and moves
            availableSets = sets;
            currentSetIndex = 0;
            updateSetSelection();
            
            // Show the selected Pokemon section and enable start button
            selectedPokemonDiv.classList.remove('hidden');
            startBattleButton.disabled = false;
            
        } catch (error) {
            console.error('Error loading Pokémon details:', error);
            pokedexEntry.textContent = 'ERROR LOADING POKÉMON DATA.';
            statsContainer.innerHTML = '<div class="text-red-400">ERROR LOADING STATS</div>';
            movesContainer.innerHTML = '<div class="text-red-400">ERROR LOADING MOVES</div>';
        }
    }
    
    // Event listeners
    pokemonInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query.length > 1) {
            fetchPokemonSuggestions(query);
        } else {
            suggestionsDiv.classList.add('hidden');
            selectedPokemonDiv.classList.add('hidden');
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!suggestionsDiv.contains(e.target) && e.target !== pokemonInput) {
            suggestionsDiv.classList.add('hidden');
        }
    });
    
    // Form submission for search
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = pokemonInput.value.trim();
        if (query) {
            fetchPokemonDetails(query);
        }
    });
    
    // Set navigation event listeners
    prevSetButton.addEventListener('click', () => {
        if (currentSetIndex > 0) {
            currentSetIndex--;
            updateSetSelection();
        }
    });
    
    nextSetButton.addEventListener('click', () => {
        if (currentSetIndex < availableSets.length - 1) {
            currentSetIndex++;
            updateSetSelection();
        }
    });
    
    // Start battle button click handler
    startBattleButton.addEventListener('click', () => {
        if (!selectedPokemon) return;
        
        // Disable the button to prevent multiple clicks
        startBattleButton.disabled = true;
        startBattleButton.textContent = 'STARTING BATTLE...';
        
        // Submit the form to start the battle
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/start';  // Matches the Flask route
        
        const pokemonInput = document.createElement('input');
        pokemonInput.type = 'hidden';
        pokemonInput.name = 'pokemon';
        pokemonInput.value = selectedPokemon.name;
        
        const setInput = document.createElement('input');
        setInput.type = 'hidden';
        setInput.name = 'selected_set';
        setInput.value = JSON.stringify(availableSets[currentSetIndex]);
        
        form.appendChild(pokemonInput);
        form.appendChild(setInput);
        document.body.appendChild(form);
        form.submit();  // This will redirect to battle.html after form submission
    });
});
