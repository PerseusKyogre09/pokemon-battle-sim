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
    
    // Display selected Pokémon
    function showSelectedPokemon(pokemon) {
        selectedPokemon = pokemon;
        selectedSprite.src = pokemon.sprites.front_default;
        selectedName.textContent = pokemon.name;
        selectedTypes.textContent = pokemon.types.map(t => t.type.name).join(', ');
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
