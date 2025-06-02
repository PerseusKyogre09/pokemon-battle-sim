document.addEventListener('DOMContentLoaded', function() {
    const pokemonInput = document.getElementById('pokemon-input');
    const suggestionsDiv = document.getElementById('suggestions');
    const form = document.getElementById('pokemon-form');
    const selectedPokemonDiv = document.getElementById('selected-pokemon');
    const selectedSprite = document.getElementById('selected-sprite');
    const selectedName = document.getElementById('selected-name');
    const selectedTypes = document.getElementById('selected-types');
    const startButton = document.getElementById('start-button');
    
    let selectedPokemon = null;
    
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
        
        const lowerQuery = query.toLowerCase();
        const isUrshifuSearch = lowerQuery.includes('urshifu');
        
        // If it's an Urshifu search, we'll handle it specially
        if (isUrshifuSearch) {
            try {
                // Fetch both Urshifu forms
                const [singleStrikeRes, rapidStrikeRes] = await Promise.all([
                    fetch('https://pokeapi.co/api/v2/pokemon/urshifu-single-strike'),
                    fetch('https://pokeapi.co/api/v2/pokemon/urshifu-rapid-strike')
                ]);
                
                const forms = [];
                
                if (singleStrikeRes.ok) {
                    forms.push(await singleStrikeRes.json());
                }
                if (rapidStrikeRes.ok) {
                    forms.push(await rapidStrikeRes.json());
                }
                
                if (forms.length > 0) {
                    // If it's an exact match for one form, select it and show the other as suggestion
                    const exactMatch = forms.find(p => p.name === lowerQuery);
                    if (exactMatch) {
                        showSelectedPokemon(exactMatch);
                        const otherForms = forms.filter(p => p.name !== lowerQuery);
                        if (otherForms.length > 0) {
                            showSuggestions(otherForms);
                        }
                    } else {
                        // Just show both forms as suggestions
                        showSuggestions(forms);
                    }
                }
                return;
            } catch (error) {
                console.error('Error fetching Urshifu forms:', error);
            }
        }
        
        // For non-Urshifu searches or if Urshifu fetch failed
        try {
            // First try exact match
            const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${lowerQuery}`);
            if (response.ok) {
                const data = await response.json();
                showSelectedPokemon(data);
                return;
            }
        } catch (error) {
            console.error('Error fetching Pokémon:', error);
        }
        
        // If no exact match, try search
        try {
            const response = await fetch(`https://pokeapi.co/api/v2/pokemon?limit=1000`);
            if (response.ok) {
                const data = await response.json();
                const matches = data.results.filter(pokemon => 
                    pokemon.name.includes(lowerQuery)
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
            div.className = 'px-4 py-2 hover:bg-gray-600 cursor-pointer capitalize';
            div.textContent = pokemon.name;
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
                const data = await response.json();
                return data;
            }
        } catch (error) {
            console.error('Error fetching Pokémon species:', error);
        }
        return null;
    }

    // Format Pokedex entry text
    function formatPokedexEntry(entry) {
        // Replace form feed characters with spaces and clean up text
        return entry
            .replace(/\f/g, ' ')
            .replace(/\n/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    // Get English Pokedex entry
    function getEnglishEntry(entries) {
        const entry = entries.find(e => e.language.name === 'en');
        return entry ? formatPokedexEntry(entry.flavor_text) : 'No Pokedex entry available.';
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

    // Fetch moves for a Pokémon
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
            
            // If no moves found in local data, try to get moves from the PokeAPI
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

    // Display selected Pokémon with all details
    async function showSelectedPokemon(pokemon) {
        selectedPokemon = pokemon;
        
        // Set basic info
        selectedSprite.src = pokemon.sprites.other['official-artwork'].front_default || 
                            pokemon.sprites.front_default;
        selectedName.textContent = pokemon.name.charAt(0).toUpperCase() + pokemon.name.slice(1);
        
        // Set Pokemon ID
        document.getElementById('pokemon-id').textContent = `#${String(pokemon.id).padStart(3, '0')}`;
        
        // Set types with badges
        selectedTypes.innerHTML = '';
        pokemon.types.forEach(typeInfo => {
            const type = typeInfo.type.name;
            const typeBadge = document.createElement('span');
            typeBadge.className = `type-badge type-${type}`;
            typeBadge.textContent = type.toUpperCase();
            selectedTypes.appendChild(typeBadge);
        });

        // Clear previous content
        document.getElementById('pokedex-entry').textContent = 'Loading...';
        document.getElementById('stats-container').innerHTML = 'Loading...';
        document.getElementById('moves-container').innerHTML = 'Loading...';

        // Fetch data in parallel
        const [speciesData, moves] = await Promise.all([
            fetchPokemonSpecies(pokemon.id),
            fetchPokemonMoves(pokemon.name)
        ]);

        // Set Pokedex entry
        const pokedexEntry = speciesData ? getEnglishEntry(speciesData.flavor_text_entries) : 'No Pokedex entry available.';
        document.getElementById('pokedex-entry').textContent = pokedexEntry;

        // Set stats
        const statsContainer = document.getElementById('stats-container');
        statsContainer.innerHTML = '';
        
        pokemon.stats.forEach(statInfo => {
            const statName = statInfo.stat.name;
            const baseStat = statInfo.base_stat;
            
            const statItem = document.createElement('div');
            statItem.className = 'stat-item';
            statItem.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="stat-label">${formatStatName(statName)}</span>
                    <span class="stat-value">${baseStat}</span>
                </div>
                <div class="stat-bar">
                    <div class="stat-bar-fill" style="width: ${Math.min(100, (baseStat / 255) * 100)}%; background: ${getStatColor(baseStat)}"></div>
                </div>
            `;
            statsContainer.appendChild(statItem);
        });

        // Set moves
        const movesContainer = document.getElementById('moves-container');
        movesContainer.innerHTML = '';
        
        moves.forEach(move => {
            const moveElement = document.createElement('div');
            moveElement.className = 'bg-gray-700 rounded-md p-2 text-center text-sm font-medium capitalize';
            moveElement.textContent = move;
            movesContainer.appendChild(moveElement);
        });

        // Show the card and enable start button
        selectedPokemonDiv.classList.remove('hidden');
        startButton.disabled = false;
    }
    
    // Event listeners
    pokemonInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query.length > 1) {
            fetchPokemonSuggestions(query);
        } else {
            suggestionsDiv.classList.add('hidden');
            selectedPokemonDiv.classList.add('hidden');
            startButton.disabled = true;
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!suggestionsDiv.contains(e.target) && e.target !== pokemonInput) {
            suggestionsDiv.classList.add('hidden');
        }
    });
    
    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedPokemon) return;
        
        // The form will submit to the server with the selected Pokémon
        form.submit();
    });
    
    // Initially disable the start button
    startButton.disabled = true;
});
