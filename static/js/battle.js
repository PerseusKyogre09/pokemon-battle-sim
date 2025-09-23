// Function to update PP display for a move
function updateMovePP(moveName, newPP) {
    console.log(`Updating PP for ${moveName} to ${newPP}`);
    const moveButtons = document.querySelectorAll('.move-button');
    let found = false;
    moveButtons.forEach(button => {
        if (button.textContent.toLowerCase().includes(moveName.toLowerCase())) {
            const ppText = button.querySelector('.pp-text');
            const ppBar = button.querySelector('.pp-bar');
            const maxPP = parseInt(button.getAttribute('data-max-pp'));
            
            if (ppText) {
                ppText.textContent = `${newPP}/${maxPP} PP`;
            }
            
            if (ppBar) {
                const percentage = Math.max(0, (newPP / maxPP) * 100);
                ppBar.style.width = `${percentage}%`;
                
                // Change color based on PP level
                if (percentage < 25) {
                    ppBar.style.backgroundColor = '#e74c3c'; // Red for low PP
                } else if (percentage < 50) {
                    ppBar.style.backgroundColor = '#f39c12'; // Orange for medium PP
                } else {
                    ppBar.style.backgroundColor = '#3498db'; // Blue for high PP
                }
                
                // Disable button if no PP left
                if (newPP <= 0) {
                    button.disabled = true;
                    button.style.opacity = 0.5;
                    button.style.cursor = 'not-allowed';
                }
            }
        }
    });
}

// Global variables to track game state
let isTurnInProgress = false;
let battleLogEl;
let battleStarted = false; // Set to false initially until animation completes
let selectedMove = null; // Track currently selected move for turn order preview

// Initialize the battle when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, initializing battle...');
    
    battleLogEl = document.getElementById("battle-log");
    if (!battleLogEl) {
        console.error('Battle log element not found!');
    } else {
        console.log('Battle log element found');
    }
    
    // Start with an empty battle log
    addLogMessage("Battle started! Choose your move.");
    
    // Initialize status displays
    console.log('Initializing status displays...');
    // Pass raw data to updateStatusDisplay - validation will happen inside the function
    updateStatusDisplay('player', window.playerStatusEffects);
    updateStatusDisplay('opponent', window.opponentStatusEffects);
    
    // Initialize PP bars for all moves
    console.log('Initializing PP bars...');
    document.querySelectorAll('.move-button').forEach(button => {
        console.log('Processing move button:', button.textContent.trim());
        const currentPP = parseInt(button.getAttribute('data-pp'));
        const maxPP = parseInt(button.getAttribute('data-max-pp'));
        const ppBar = button.querySelector('.pp-bar');
        const ppText = button.querySelector('.pp-text');
        
        console.log(`  - Current PP: ${currentPP}, Max PP: ${maxPP}`);
        if (ppBar) {
            const percentage = Math.max(0, (currentPP / maxPP) * 100);
            console.log(`  - PP Percentage: ${percentage}%`);
            ppBar.style.width = `${percentage}%`;
            
            // Set initial color based on PP level
            if (percentage < 25) {
                ppBar.style.backgroundColor = '#e74c3c'; // Red for low PP
            } else if (percentage < 50) {
                ppBar.style.backgroundColor = '#f39c12'; // Orange for medium PP
            } else {
                ppBar.style.backgroundColor = '#3498db'; // Blue for high PP
            }
            
            // Disable button if no PP left
            if (currentPP <= 0) {
                button.disabled = true;
                button.style.opacity = 0.5;
                button.style.cursor = 'not-allowed';
            }
        }
        
        if (ppText) {
            ppText.textContent = `${currentPP}/${maxPP} PP`;
        }
    });
    
    // Set initial health bars
    const playerHealthBar = document.getElementById("player-health-bar");
    const opponentHealthBar = document.getElementById("opponent-health-bar");
    
    if (playerHealthBar && opponentHealthBar) {
        const playerHpElement = document.getElementById("player-hp");
        const opponentHpElement = document.getElementById("opponent-hp");
        
        if (playerHpElement && opponentHpElement) {
            const playerHpText = playerHpElement.textContent.trim();
            const opponentHpText = opponentHpElement.textContent.trim();
            
            const [playerHp, playerMaxHp] = playerHpText.split('/');
            const [opponentHp, opponentMaxHp] = opponentHpText.split('/');
            
            updateHealthBar('#player-health-bar', parseInt(playerHp), parseInt(playerMaxHp));
            updateHealthBar('#opponent-health-bar', parseInt(opponentHp), parseInt(opponentMaxHp));
        } else {
            console.error('Health text elements not found');
        }
    } else {
        console.error('Health bar elements not found');
    }
    
    // Initialize priority display
    console.log('Initializing priority display...');
    try {
        displayPriorityValues();
        updateMoveButtonInteractions();
    } catch (error) {
        console.error('Error initializing priority display:', error);
    }
    
    // Get DOM elements and store in a global object for the function
    const elements = {
        playerPokemon: document.getElementById('player'),
        opponentPokemon: document.getElementById('opponent'),
        playerHealthContainer: document.querySelector('.player-health-container'),
        opponentHealthContainer: document.querySelector('.opponent-health-container'),
        moveButtons: document.querySelectorAll('.move-button'),
        flashElement: document.getElementById('flash-element'),
        playerPokeball: document.getElementById('player-pokeball'),
        opponentPokeball: document.getElementById('opponent-pokeball'),
        opponentCry: document.getElementById('opponent-cry'),
        playerCry: document.getElementById('player-cry')
    };
    
    // Make elements available to all scopes in this function
    const {
        playerPokemon,
        opponentPokemon,
        playerHealthContainer,
        opponentHealthContainer,
        moveButtons,
        flashElement,
        playerPokeball,
        opponentPokeball,
        opponentCry,
        playerCry
    } = elements;
    
    console.log('Hiding elements - Player Pokemon:', !!playerPokemon, 
                'Opponent Pokemon:', !!opponentPokemon,
                'Player Health:', !!playerHealthContainer,
                'Opponent Health:', !!opponentHealthContainer);
    
    // Hide elements initially
    const hideElement = (element, name) => {
        if (element) {
            element.classList.add('hidden-element');
            element.style.opacity = '0';
            console.log(`   - Hidden ${name}`);
        } else {
            console.log(`   - ${name} element not found`);
        }
    };
    
    hideElement(playerPokemon, 'player Pokémon');
    hideElement(opponentPokemon, 'opponent Pokémon');
    hideElement(playerHealthContainer, 'player health bar');
    hideElement(opponentHealthContainer, 'opponent health bar');
    hideElement(flashElement, 'flash element');
    
    // Disable move buttons until animation completes
    if (moveButtons.length > 0) {
        moveButtons.forEach(button => {
            button.disabled = true;
            button.style.opacity = 0.5;
        });
    } else {
        console.warn('No move buttons found!');
    }
    
    // Initialize PP bars
    document.querySelectorAll('.pp-bar[data-pp-percent]').forEach(bar => {
        const percent = bar.getAttribute('data-pp-percent');
        if (percent) {
            bar.style.width = `${percent}%`;
        }
    });
    
    // Start the battle sequence with animations
    console.log('Starting battle sequence...');
    // Add a small delay to ensure all elements are properly initialized
    setTimeout(() => {
        startBattleSequence().catch(error => {
            console.error('Error in battle sequence:', error);
        });
    }, 500);
});

// Function to load and play a Pokémon cry
function loadPokemonCry(audioElement, pokemonName, distorted = false) {
    const formattedName = pokemonName.toLowerCase();
    audioElement.src = `/pokemon/cry/${formattedName}`;
    
    if (distorted) {
        // Apply distortion effect for fainting
        audioElement.playbackRate = 0.7;
        audioElement.preservesPitch = false;
    } else {
        // Reset to normal playback
        audioElement.playbackRate = 1.0;
        audioElement.preservesPitch = true;
    }
    
    // Play the cry
    audioElement.play().catch(error => {
        console.error('Error playing Pokémon cry:', error);
    });
}

// Start the battle sequence with animations
async function startBattleSequence() {
    console.log('Battle sequence started');
    try {
        console.log('1. Starting battle music...');
        // Start battle music
        const battleMusic = document.getElementById('battle-music');
        if (battleMusic) {
            console.log('   - Battle music element found, setting volume...');
            battleMusic.volume = 0.7;
            console.log('   - Attempting to play music...');
            try {
                await battleMusic.play();
                console.log('   - Music started successfully');
            } catch (error) {
                console.log('   - Music play failed:', error);
            }
        } else {
            console.log('   - Battle music element not found');
        }
        
        // Wait a moment before starting animations
        console.log('2. Waiting before starting animations...');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        console.log('3. Showing Pokéballs...');
        // Show the pokeballs
        const playerPokeball = document.getElementById('player-pokeball');
        const opponentPokeball = document.getElementById('opponent-pokeball');
        
        console.log('   - Player Pokéball element:', playerPokeball ? 'found' : 'not found');
        console.log('   - Opponent Pokéball element:', opponentPokeball ? 'found' : 'not found');
        
        if (playerPokeball) {
            console.log('   - Setting player Pokéball opacity to 1');
            playerPokeball.style.opacity = '1';
        }
        
        if (opponentPokeball) {
            console.log('   - Setting opponent Pokéball opacity to 1');
            opponentPokeball.style.opacity = '1';
        }
        
        // Get the Pokémon elements
        const playerPokemon = document.getElementById('player');
        const opponentPokemon = document.getElementById('opponent');
        
        // Get the flash element
        const flashElement = document.getElementById('flash-element');
        
        // Throw opponent's Pokéball first
        console.log('4. Starting opponent\'s Pokéball throw...');
        if (opponentPokeball) {
            console.log('   - Playing Pokéball throw sound...');
            // Play the Pokéball throw sound for opponent's Pokémon
            const pokeballSound = document.getElementById('pokeball-sound');
            if (pokeballSound) {
                try {
                    await pokeballSound.play();
                    console.log('   - Pokéball sound played successfully');
                } catch (error) {
                    console.log('   - Pokeball sound failed:', error);
                }
            } else {
                console.log('   - Pokéball sound element not found');
            }
            
            console.log('   - Starting throw animation...');
            // Animate opponent's Pokéball throw
            opponentPokeball.style.animation = 'throwOpponent 1s forwards';
            
            // Wait for the throw animation to complete
            console.log('   - Waiting for throw animation to complete...');
            await new Promise(resolve => setTimeout(resolve, 1000));
            console.log('   - Throw animation complete');
            
            // Flash the screen
            console.log('5. Starting flash animation...');
            if (flashElement) {
                console.log('   - Flash element found, displaying flash...');
                flashElement.style.display = 'block';
                flashElement.style.animation = 'flash 0.3s';
                
                // Wait for the flash
                console.log('   - Waiting for flash to complete...');
                await new Promise(resolve => setTimeout(resolve, 300));
                
                // Show opponent's Pokémon
                console.log('6. Showing opponent\'s Pokémon...');
                if (opponentPokemon) {
                    console.log('   - Opponent Pokémon element found, making visible');
                    // Remove hidden-element class if present
                    opponentPokemon.classList.remove('hidden-element');
                    // Reset any previous animations
                    opponentPokemon.style.animation = 'none';
                    // Force reflow to restart animation
                    void opponentPokemon.offsetWidth;
                    // Apply the appear animation
                    opponentPokemon.style.animation = 'appearPokemon 0.8s forwards';
                    opponentPokemon.style.opacity = '1';
                    opponentPokemon.style.display = 'block';
                    console.log('   - Applied animation to opponent Pokémon');
                    
                    // Show opponent's health bar after a short delay
                    const showOpponentHealth = () => {
                        console.log('   - Showing opponent\'s health bar...');
                        const container = document.querySelector('.opponent-health-container');
                        if (container) {
                            container.classList.remove('hidden-element');
                            container.style.opacity = '1';
                            container.style.display = 'block';
                            console.log('   - Opponent health bar shown');
                        } else {
                            console.log('   - Opponent health container not found');
                        }
                    };
                    setTimeout(showOpponentHealth, 300);
                } else {
                    console.log('   - Opponent Pokémon element not found');
                }
                    
                // Play opponent's cry
                console.log('7. Playing opponent\'s cry...');
                const opponentCry = document.getElementById('opponent-cry');
                if (opponentCry) {
                    try {
                        // Get the opponent's name from the data attribute
                        const opponentName = opponentCry.getAttribute('data-pokemon');
                        if (opponentName) {
                            console.log(`   - Loading cry for ${opponentName}...`);
                            // Get the Pokémon ID from the cry element's data attribute or use a default
                            const pokemonId = opponentCry.getAttribute('data-pokemon-id') || '6'; // Default to Charizard if not found
                            const cryPath = `https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/${pokemonId}.ogg`;
                            console.log('   - Loading cry from:', cryPath);
                            
                            try {
                                // Create a new audio element to avoid issues with loading
                                const audio = new Audio(cryPath);
                                audio.volume = 0.5;
                                
                                // Play the cry
                                const playPromise = audio.play();
                                if (playPromise !== undefined) {
                                    await playPromise.catch(e => {
                                        console.log('   - Error playing cry (will continue):', e.message);
                                        return Promise.resolve();
                                    });
                                }
                                
                                console.log('   - Opponent cry playback started');
                                
                                // Wait for the cry to finish or timeout after 2 seconds
                                await Promise.race([
                                    new Promise(resolve => {
                                        audio.onended = resolve;
                                    }),
                                    new Promise(resolve => setTimeout(resolve, 2000))
                                ]);
                                
                                console.log('   - Opponent cry sequence complete');
                            } catch (error) {
                                console.log('   - Error with cry playback (continuing):', error.message);
                            }
                        } else {
                            console.log('   - No opponent name found in data attribute');
                        }
                    } catch (error) {
                        console.log('   - Opponent cry failed:', error.message);
                    }
                } else {
                    console.log('   - Opponent cry element not found');
                }
                
                // Hide the flash
                console.log('8. Hiding flash...');
                await new Promise(resolve => setTimeout(resolve, 300));
                flashElement.style.display = 'none';
                console.log('   - Flash hidden');
            } else {
                console.log('   - Flash element not found');
            }
        }
        
        // Wait a moment before player's turn
        console.log('9. Waiting before player\'s turn...');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Throw player's Pokéball
        console.log('10. Starting player\'s Pokéball throw...');
        if (playerPokeball) {
            // Play the Pokéball throw sound for player's Pokémon
            console.log('    - Playing Pokéball throw sound...');
            const pokeballSound = document.getElementById('pokeball-sound');
            if (pokeballSound) {
                try {
                    pokeballSound.currentTime = 0;
                    await pokeballSound.play();
                    console.log('    - Pokéball sound played successfully');
                } catch (error) {
                    console.log('    - Pokeball sound failed:', error);
                }
            } else {
                console.log('    - Pokéball sound element not found');
            }
            
            // Animate player's Pokéball throw
            console.log('    - Starting player throw animation...');
            playerPokeball.style.animation = 'throwPlayer 1s forwards';
            
            // Wait for the throw animation to complete
            console.log('    - Waiting for throw animation to complete...');
            await new Promise(resolve => setTimeout(resolve, 1000));
            console.log('    - Player throw animation complete');
            
            // Flash the screen
            console.log('11. Starting flash animation for player...');
            if (flashElement) {
                console.log('    - Flash element found, displaying flash...');
                flashElement.style.display = 'block';
                flashElement.style.animation = 'flash 0.3s';
                
                // Wait for the flash
                console.log('    - Waiting for flash to complete...');
                await new Promise(resolve => setTimeout(resolve, 300));
                
                // Show player's Pokémon
                console.log('12. Showing player\'s Pokémon...');
                if (playerPokemon) {
                    console.log('    - Player Pokémon element found, making visible');
                    // Remove hidden-element class if present
                    playerPokemon.classList.remove('hidden-element');
                    // Reset any previous animations
                    playerPokemon.style.animation = 'none';
                    // Force reflow to restart animation
                    void playerPokemon.offsetWidth;
                    // Apply the appear animation
                    playerPokemon.style.animation = 'appearPokemon 0.8s forwards';
                    playerPokemon.style.opacity = '1';
                    playerPokemon.style.display = 'block';
                    console.log('    - Applied animation to player Pokémon');
                    
                    // Show player's health bar after a short delay
                    const showPlayerHealth = () => {
                        console.log('    - Showing player\'s health bar...');
                        const container = document.querySelector('.player-health-container');
                        if (container) {
                            container.classList.remove('hidden-element');
                            container.style.opacity = '1';
                            container.style.display = 'block';
                            console.log('    - Player health bar shown');
                        } else {
                            console.log('    - Player health container not found');
                        }
                    };
                    setTimeout(showPlayerHealth, 300);
                } else {
                    console.log('    - Player Pokémon element not found');
                }
                
                // Play player's cry
                console.log('13. Playing player\'s cry...');
                const playerCry = document.getElementById('player-cry');
                if (playerCry) {
                    try {
                        // Get the Pokémon ID from the cry element's data attribute or use a default
                        const pokemonId = playerCry.getAttribute('data-pokemon-id') || '6'; // Default to Charizard if not found
                        const cryPath = `https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/${pokemonId}.ogg`;
                        console.log('    - Loading player cry from:', cryPath);
                        
                        // Create a new audio element to avoid issues with loading
                        const audio = new Audio(cryPath);
                        audio.volume = 0.5;
                        
                        // Play the cry
                        const playPromise = audio.play();
                        if (playPromise !== undefined) {
                            await playPromise.catch(e => {
                                console.log('    - Error playing player cry (will continue):', e.message);
                                return Promise.resolve();
                            });
                        }
                        
                        console.log('    - Player cry playback started');
                        
                        // Wait for the cry to finish or timeout after 2 seconds
                        await Promise.race([
                            new Promise(resolve => {
                                audio.onended = resolve;
                            }),
                            new Promise(resolve => setTimeout(resolve, 2000))
                        ]);
                        
                        console.log('    - Player cry sequence complete');
                    } catch (error) {
                        console.log('    - Error with player cry playback (continuing):', error.message);
                    }
                } else {
                    console.log('    - Player cry element not found');
                }
                
                // Hide the flash
                console.log('14. Hiding flash...');
                await new Promise(resolve => setTimeout(resolve, 300));
                flashElement.style.display = 'none';
                console.log('    - Flash hidden');
            } else {
                console.log('    - Flash element not found');
            }
        }
        
        // Enable move buttons after animations complete
        console.log('15. Enabling move buttons...');
        const moveButtons = document.querySelectorAll('.move-button');
        if (moveButtons.length > 0) {
            console.log(`    - Found ${moveButtons.length} move buttons, enabling them...`);
            moveButtons.forEach((button, index) => {
                button.disabled = false;
                button.style.opacity = '1';
                console.log(`    - Button ${index + 1} enabled`);
            });
        } else {
            console.log('    - No move buttons found!');
        }
        
        console.log('16. Battle sequence completed successfully!');
    } catch (error) {
        console.error('Error in battle sequence:', error);
    } finally {
        // Set battle as started
        console.log('17. Setting battle as started');
        battleStarted = true;
        console.log('18. Battle started flag set to:', battleStarted);
        
        // Initialize priority display after battle starts
        console.log('19. Initializing priority display after battle start...');
        try {
            displayPriorityValues();
            updateMoveButtonInteractions();
        } catch (error) {
            console.error('Error initializing priority display:', error);
        }
    }
}

function updateHealthBar(selector, currentHp, maxHp) {
    const healthBar = document.querySelector(selector);
    if (!healthBar) {
        console.error(`Health bar not found with selector: ${selector}`);
        return;
    }
    
    // Ensure HP values are within bounds
    currentHp = Math.max(0, Math.min(currentHp, maxHp));
    const healthPercentage = (currentHp / maxHp) * 100;
    
    // Update the health bar width with smooth transition
    healthBar.style.width = `${healthPercentage}%`;
    
    // Update health bar color class based on percentage
    healthBar.classList.remove('medium', 'low');
    if (healthPercentage <= 20) {
        healthBar.classList.add('low');
    } else if (healthPercentage <= 50) {
        healthBar.classList.add('medium');
    }
    
    // Update the HP text display
    const barId = selector.replace('#', ''); // Remove '#' from selector if present
    const pokemonType = barId.includes('player') ? 'player' : 'opponent';
    const hpTextElement = document.getElementById(`${pokemonType}-hp`);
    
    if (hpTextElement) {
        hpTextElement.textContent = `${Math.round(currentHp)}/${maxHp}`;
        console.log(`Updated ${pokemonType} HP text to: ${Math.round(currentHp)}/${maxHp}`);
    } else {
        console.error(`Could not find HP text element for ${pokemonType}`);
    }
    
    console.log(`Updated ${selector} to ${healthPercentage.toFixed(1)}% (${currentHp}/${maxHp})`);
}

function clearBattleLog() {
    // Clear main battle log
    const battleLog = document.getElementById('battle-log');
    if (battleLog) {
        const logList = battleLog.querySelector('ul');
        if (logList) {
            logList.innerHTML = '';
        }
    }
    
    // Clear right-side battle log
    const rightBattleLog = document.getElementById('right-battle-log');
    if (rightBattleLog) {
        rightBattleLog.querySelector('div').innerHTML = '';
    }
}

function addLogMessage(message, isEffectiveness = false, isPlayer = null, isPriorityRelated = false) {
    const stackTrace = new Error().stack;
    console.log('=== ADDING LOG MESSAGE ===');
    console.log('Message:', message);
    console.log('isEffectiveness:', isEffectiveness);
    console.log('isPlayer:', isPlayer);
    console.log('isPriorityRelated:', isPriorityRelated);
    console.log('Call stack:', stackTrace);
    
    if (!battleLogEl) {
        console.error('Battle log element not found');
        return;
    }
    
    // Add to main battle log
    const messageEl = document.createElement('div');
    messageEl.className = 'battle-log-message';
    
    if (isEffectiveness) {
        messageEl.classList.add('effectiveness');
    } else if (isPlayer !== null) {
        messageEl.classList.add(isPlayer ? 'player' : 'opponent');
    }
    
    messageEl.textContent = message;
    console.log('Adding element to main log:', message);
    battleLogEl.appendChild(messageEl);
    battleLogEl.scrollTop = battleLogEl.scrollHeight;
    
    // Update the battle log text at the top
    const battleLogText = document.getElementById('battle-log-text');
    if (battleLogText) {
        if (isPriorityRelated) {
            battleLogText.innerHTML = `<span style="color: #f1c40f;">${message}</span>`;
        } else {
            battleLogText.textContent = message;
        }
    }
    
    // Add to the right-side battle log panel
    const rightBattleLog = document.getElementById('right-battle-log');
    if (rightBattleLog) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        // Add appropriate class based on message type
        if (isPriorityRelated) {
            logEntry.classList.add('priority-message');
            logEntry.textContent = message;
            logEntry.style.color = '#f1c40f';
            logEntry.style.borderLeftColor = '#f1c40f';
        } else if (isEffectiveness) {
            logEntry.classList.add('effectiveness');
            logEntry.textContent = message;
        } else if (isPlayer === true) {
            logEntry.classList.add('player-move');
            logEntry.textContent = message;
        } else if (isPlayer === false) {
            logEntry.classList.add('opponent-move');
            logEntry.textContent = message;
        } else {
            logEntry.textContent = message;
        }
        
        rightBattleLog.querySelector('div').appendChild(logEntry);
        rightBattleLog.scrollTop = rightBattleLog.scrollHeight;
    }
    
    console.log('=== MESSAGE ADDED ===');
}

// Status effect validation function
function validateStatusEffects(statusEffects) {
    console.log('=== VALIDATING STATUS EFFECTS ===');
    console.log('Input:', statusEffects);
    
    // Handle null, undefined, or non-array inputs
    if (!statusEffects) {
        console.log('Status effects is null/undefined, returning empty array');
        return [];
    }
    
    if (!Array.isArray(statusEffects)) {
        console.warn('Status effects is not an array:', typeof statusEffects, statusEffects);
        return [];
    }
    
    // Validate each status effect object
    const validatedEffects = statusEffects.filter(status => {
        if (!status || typeof status !== 'object') {
            console.warn('Invalid status effect (not an object):', status);
            return false;
        }
        
        // Check required properties
        if (!status.type || typeof status.type !== 'string') {
            console.warn('Status effect missing or invalid type:', status);
            return false;
        }
        
        if (!status.name || typeof status.name !== 'string') {
            console.warn('Status effect missing or invalid name:', status);
            return false;
        }
        
        // Validate optional properties with defaults
        if (status.is_major !== undefined && typeof status.is_major !== 'boolean') {
            console.warn('Status effect has invalid is_major property:', status);
            status.is_major = true; // Default to major status
        }
        
        if (status.duration !== undefined && (typeof status.duration !== 'number' || isNaN(status.duration))) {
            console.warn('Status effect has invalid duration:', status);
            status.duration = -1; // Default to permanent
        }
        
        if (status.counter !== undefined && (typeof status.counter !== 'number' || isNaN(status.counter))) {
            console.warn('Status effect has invalid counter:', status);
            status.counter = 0; // Default counter
        }
        
        return true;
    });
    
    console.log(`Validated ${validatedEffects.length} out of ${statusEffects.length} status effects`);
    console.log('=== END STATUS VALIDATION ===');
    
    return validatedEffects;
}

// Status effect display functions
function updateStatusDisplay(pokemonType, statusEffects) {
    console.log(`=== STATUS DISPLAY UPDATE ===`);
    console.log(`Pokemon: ${pokemonType}`);
    console.log(`New status effects (raw):`, statusEffects);
    
    // Validate status effects data before processing
    const validatedStatusEffects = validateStatusEffects(statusEffects);
    console.log(`Validated status effects:`, validatedStatusEffects);
    
    const statusContainer = document.getElementById(`${pokemonType}-status-indicators`);
    if (!statusContainer) {
        console.error(`Status container not found for ${pokemonType}`);
        return;
    }
    
    // Get current status effects for comparison
    const currentIndicators = Array.from(statusContainer.querySelectorAll('.status-indicator'));
    const currentStatuses = currentIndicators.map(indicator => {
        const classList = Array.from(indicator.classList);
        // Find the status type class (not 'status-indicator' or 'fade-in')
        const statusType = classList.find(cls => cls !== 'status-indicator' && cls !== 'fade-in');
        return statusType;
    }).filter(Boolean);
    
    console.log(`Current status effects for ${pokemonType}:`, currentStatuses);
    
    // Determine what's being added and removed using validated data
    const newStatuses = validatedStatusEffects.map(status => status.type);
    const addedStatuses = newStatuses.filter(status => !currentStatuses.includes(status));
    const removedStatuses = currentStatuses.filter(status => !newStatuses.includes(status));
    
    // Log status changes
    if (addedStatuses.length > 0) {
        console.log(`✅ Status effects ADDED to ${pokemonType}:`, addedStatuses);
    }
    if (removedStatuses.length > 0) {
        console.log(`❌ Status effects REMOVED from ${pokemonType}:`, removedStatuses);
    }
    if (addedStatuses.length === 0 && removedStatuses.length === 0) {
        console.log(`🔄 No status changes for ${pokemonType}`);
    }
    
    // Enhanced status indicator management - remove indicators that are no longer active
    if (removedStatuses.length > 0) {
        console.log(`Removing ${removedStatuses.length} status indicators with animations`);
        // Don't await here to avoid blocking the UI update
        removeMultipleStatusIndicators(pokemonType, removedStatuses).catch(error => {
            console.error('Error removing status indicators:', error);
        });
    }
    
    // Add only new status indicators (don't clear existing ones)
    if (addedStatuses.length > 0) {
        console.log(`Adding ${addedStatuses.length} new status indicators for ${pokemonType}`);
        addedStatuses.forEach(statusType => {
            const statusData = validatedStatusEffects.find(s => s.type === statusType);
            if (statusData) {
                console.log(`  Adding ${statusType} (${statusData.name})`);
                const indicator = createStatusIndicator(statusData);
                statusContainer.appendChild(indicator);
            }
        });
    }
    
    // Clear all indicators only if there are no status effects
    if (validatedStatusEffects.length === 0 && currentStatuses.length > 0) {
        console.log(`No active status effects for ${pokemonType} - clearing container`);
        statusContainer.innerHTML = '';
    }
    
    console.log(`=== END STATUS DISPLAY UPDATE ===`);
}

function createStatusIndicator(status) {
    const indicator = document.createElement('div');
    indicator.className = `status-indicator ${status.type} fade-in`;
    indicator.textContent = getStatusAbbreviation(status.type);
    indicator.title = `${status.name}${status.duration > 0 ? ` (${status.duration} turns)` : ''}`;
    
    return indicator;
}

function getStatusAbbreviation(statusType) {
    const abbreviations = {
        'burn': 'BRN',
        'paralysis': 'PAR',
        'freeze': 'FRZ',
        'sleep': 'SLP',
        'poison': 'PSN',
        'toxic': 'TOX'
    };
    
    return abbreviations[statusType] || statusType.toUpperCase().substring(0, 3);
}

function addStatusIndicator(pokemonType, status) {
    console.log(`Adding status indicator for ${pokemonType}:`, status);
    
    const statusContainer = document.getElementById(`${pokemonType}-status-indicators`);
    if (!statusContainer) {
        console.error(`Status container not found for ${pokemonType}`);
        return;
    }
    
    // Check if status already exists
    const existingIndicator = statusContainer.querySelector(`.status-indicator.${status.type}`);
    if (existingIndicator) {
        console.log(`Status ${status.type} already exists for ${pokemonType}`);
        return;
    }
    
    const indicator = createStatusIndicator(status);
    statusContainer.appendChild(indicator);
}

// Enhanced function to remove multiple status indicators with proper cleanup
async function removeMultipleStatusIndicators(pokemonType, statusTypesToRemove) {
    console.log(`=== REMOVING MULTIPLE STATUS INDICATORS ===`);
    console.log(`Pokemon: ${pokemonType}, Statuses to remove:`, statusTypesToRemove);
    
    if (!Array.isArray(statusTypesToRemove) || statusTypesToRemove.length === 0) {
        console.log('No status indicators to remove');
        return Promise.resolve();
    }
    
    // Remove all indicators in parallel and wait for all animations to complete
    const removalPromises = statusTypesToRemove.map(statusType => 
        removeStatusIndicator(pokemonType, statusType).catch(error => {
            console.error(`Failed to remove ${statusType}:`, error);
            // Don't let one failure stop the others
            return Promise.resolve();
        })
    );
    
    try {
        await Promise.all(removalPromises);
        console.log(`✅ All status indicators removed for ${pokemonType}`);
    } catch (error) {
        console.error(`Error removing multiple status indicators:`, error);
    }
    
    console.log(`=== END MULTIPLE REMOVAL ===`);
}

function removeStatusIndicator(pokemonType, statusType) {
    console.log(`=== REMOVING STATUS INDICATOR ===`);
    console.log(`Pokemon: ${pokemonType}, Status: ${statusType}`);
    
    // Validate input parameters
    if (!pokemonType || typeof pokemonType !== 'string') {
        console.error('Invalid pokemonType provided to removeStatusIndicator:', pokemonType);
        return Promise.reject(new Error('Invalid pokemonType'));
    }
    
    if (!statusType || typeof statusType !== 'string') {
        console.error('Invalid statusType provided to removeStatusIndicator:', statusType);
        return Promise.reject(new Error('Invalid statusType'));
    }
    
    const statusContainer = document.getElementById(`${pokemonType}-status-indicators`);
    if (!statusContainer) {
        console.error(`Status container not found for ${pokemonType}`);
        return Promise.reject(new Error(`Status container not found for ${pokemonType}`));
    }
    
    const indicator = statusContainer.querySelector(`.status-indicator.${statusType}`);
    if (!indicator) {
        console.log(`Status indicator ${statusType} not found for ${pokemonType} - already removed or never existed`);
        return Promise.resolve(); // Not an error, just already removed
    }
    
    // Return a promise that resolves when the animation completes
    return new Promise((resolve, reject) => {
        try {
            console.log(`Starting fade-out animation for ${statusType}`);
            
            // Add fade-out class for animation
            indicator.classList.add('fade-out');
            
            // Set up animation completion handler
            const handleAnimationEnd = (event) => {
                // Make sure this is the right element and animation
                if (event.target === indicator && event.animationName === 'fadeOut') {
                    console.log(`Fade-out animation completed for ${statusType}`);
                    cleanup();
                }
            };
            
            // Set up timeout as fallback in case animation events don't fire
            const timeoutId = setTimeout(() => {
                console.log(`Fade-out timeout reached for ${statusType}, forcing cleanup`);
                cleanup();
            }, 500); // Slightly longer than expected animation duration
            
            const cleanup = () => {
                try {
                    // Remove event listener
                    indicator.removeEventListener('animationend', handleAnimationEnd);
                    
                    // Clear timeout
                    clearTimeout(timeoutId);
                    
                    // Remove the indicator from DOM if it still exists
                    if (indicator.parentNode) {
                        console.log(`Removing ${statusType} indicator from DOM`);
                        indicator.parentNode.removeChild(indicator);
                    }
                    
                    console.log(`✅ Successfully removed status indicator ${statusType} for ${pokemonType}`);
                    resolve();
                } catch (cleanupError) {
                    console.error(`Error during cleanup of ${statusType}:`, cleanupError);
                    reject(cleanupError);
                }
            };
            
            // Listen for animation end event
            indicator.addEventListener('animationend', handleAnimationEnd);
            
        } catch (error) {
            console.error(`Error setting up removal animation for ${statusType}:`, error);
            reject(error);
        }
    });
}

// Enhanced status indicator lifecycle management
function clearAllStatusIndicators(pokemonType) {
    console.log(`=== CLEARING ALL STATUS INDICATORS ===`);
    console.log(`Pokemon: ${pokemonType}`);
    
    const statusContainer = document.getElementById(`${pokemonType}-status-indicators`);
    if (!statusContainer) {
        console.error(`Status container not found for ${pokemonType}`);
        return Promise.resolve();
    }
    
    // Get all current status indicators
    const indicators = Array.from(statusContainer.querySelectorAll('.status-indicator'));
    
    if (indicators.length === 0) {
        console.log(`No status indicators to clear for ${pokemonType}`);
        return Promise.resolve();
    }
    
    console.log(`Clearing ${indicators.length} status indicators for ${pokemonType}`);
    
    // Extract status types from indicators
    const statusTypes = indicators.map(indicator => {
        const classList = Array.from(indicator.classList);
        return classList.find(cls => cls !== 'status-indicator' && cls !== 'fade-in' && cls !== 'fade-out');
    }).filter(Boolean);
    
    // Use the enhanced removal function
    return removeMultipleStatusIndicators(pokemonType, statusTypes);
}

// Function to handle status indicator cleanup when Pokemon faints
async function handlePokemonFaintStatusCleanup(pokemonType) {
    console.log(`=== POKEMON FAINT STATUS CLEANUP ===`);
    console.log(`Cleaning up status indicators for fainted ${pokemonType}`);
    
    try {
        await clearAllStatusIndicators(pokemonType);
        console.log(`✅ Status cleanup completed for fainted ${pokemonType}`);
    } catch (error) {
        console.error(`Error during faint status cleanup for ${pokemonType}:`, error);
    }
    
    console.log(`=== END FAINT CLEANUP ===`);
}

function disableMoveButtons(disabled) {
    const moveButtons = document.querySelectorAll('.move-button');
    moveButtons.forEach(button => {
        button.disabled = disabled;
        if (disabled) {
            button.style.opacity = '0.5';
            button.style.cursor = 'not-allowed';
        } else {
            button.style.opacity = '';
            button.style.cursor = '';
            button.style.pointerEvents = '';
        }
    });
}

function animateAttack(isPlayer) {
    // Get the attacking Pokémon element
    const attackerElement = isPlayer ? 
        document.getElementById("player").parentElement : 
        document.getElementById("opponent").parentElement;
    
    // Get the defending Pokémon element
    const defenderElement = isPlayer ? 
        document.getElementById("opponent").parentElement : 
        document.getElementById("player").parentElement;
    
    // Add a quick "attack" animation to the attacker
    attackerElement.classList.add('translate-x-2', 'translate-y-2');
    setTimeout(() => {
        attackerElement.classList.remove('translate-x-2', 'translate-y-2');
    }, 150);
    
    // After a brief delay, "shake" the defender and play hit sound
    setTimeout(() => {
        defenderElement.classList.add('animate-shake');
        document.getElementById('hit-sound').play();
        
        setTimeout(() => {
            defenderElement.classList.remove('animate-shake');
        }, 500);
    }, 200);
}

// Function to animate a Pokémon fainting with distorted cry and status cleanup
async function animateFaint(isPlayer) {
    const pokemonElement = isPlayer ? 
        document.getElementById("player") : 
        document.getElementById("opponent");
    
    const pokemonType = isPlayer ? 'player' : 'opponent';
    
    // Get the Pokémon name from the cry audio element
    const pokemonName = isPlayer ? 
        document.getElementById('player-cry').getAttribute('data-pokemon') : 
        document.getElementById('opponent-cry').getAttribute('data-pokemon');
    
    // Play the distorted cry using the loadPokemonCry function
    const cryElement = isPlayer ? 
        document.getElementById('player-faint-cry') : 
        document.getElementById('opponent-faint-cry');
    
    // Load and play the distorted cry
    loadPokemonCry(cryElement, pokemonName, true);
    
    // Add the faint animation class
    pokemonElement.classList.add('faint-animation');
    
    // Start status cleanup immediately when faint animation begins
    const statusCleanupPromise = handlePokemonFaintStatusCleanup(pokemonType);
    
    // Return a promise that resolves when both animation and status cleanup are complete
    const animationPromise = new Promise(resolve => {
        setTimeout(() => {
            resolve();
        }, 1500); // Animation takes 1.5 seconds
    });
    
    // Wait for both the animation and status cleanup to complete
    try {
        await Promise.all([animationPromise, statusCleanupPromise]);
        console.log(`✅ Faint animation and status cleanup completed for ${pokemonType}`);
    } catch (error) {
        console.error(`Error during faint animation or status cleanup for ${pokemonType}:`, error);
        // Still resolve to not block the game flow
    }
}

async function makeMove(move) {
    // Prevent moves if battle hasn't started or a turn is in progress
    if (!battleStarted || isTurnInProgress) return;
    
    isTurnInProgress = true;
    disableMoveButtons(true);
    
    try {
        const playerPokemonName = document.getElementById('player-cry').getAttribute('data-pokemon');
        const opponentPokemonName = document.getElementById('opponent-cry').getAttribute('data-pokemon');
        
        // Get data from server about the move result
        const response = await fetch('/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ move: move })
        });
        
        const data = await response.json();
        if (!response.ok) {
            alert(data.error);
            isTurnInProgress = false;
            disableMoveButtons(false);
            return;
        }
        
        const { turn_info, player_moves_pp } = data;
        
        // Update PP for all moves from server response
        console.log('Updating PP from server response:', player_moves_pp);
        if (player_moves_pp) {
            Object.entries(player_moves_pp).forEach(([moveName, ppData]) => {
                console.log(`Updating PP for ${moveName}:`, ppData);
                updateMovePP(moveName, ppData.current_pp);
                
                // Update the max PP in the button's data attribute
                const moveButtons = document.querySelectorAll('.move-button');
                moveButtons.forEach(button => {
                    if (button.textContent.toLowerCase().includes(moveName.toLowerCase())) {
                        button.setAttribute('data-max-pp', ppData.max_pp);
                    }
                });
            });
        }
        
        // Process all battle events at once, with faint events handled last
        if (turn_info.battle_events && turn_info.battle_events.length > 0) {
            // Sort events by timestamp to ensure correct order
            const sortedEvents = [...turn_info.battle_events].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
            
            // Process all events at once - faint events will be handled last
            const battleOver = await processMoveEvent(sortedEvents, data);
            
            // Update HP bars after processing all events
            updateHealthBar('#player-health-bar', data.player_hp, data.player_max_hp);
            updateHealthBar('#opponent-health-bar', data.opponent_hp, data.opponent_max_hp);
            
            // Update status displays - always call to ensure synchronization
            try {
                console.log('Updating status displays after move response');
                // Pass raw data to updateStatusDisplay - validation will happen inside the function
                updateStatusDisplay('player', data.player_status_effects);
                updateStatusDisplay('opponent', data.opponent_status_effects);
            } catch (error) {
                console.error('Error updating status displays:', error);
                // Attempt to update with empty arrays as fallback
                updateStatusDisplay('player', []);
                updateStatusDisplay('opponent', []);
            }
            
            // Check if battle is over after processing all events
            if (battleOver) {
                disableMoveButtons(true);
                return;
            }
        }
        
        // Final check for game over after all events
        if (data.is_game_over) {
            disableMoveButtons(true);
            return;
        }
        
    } finally {
        // Turn complete - re-enable buttons after a short delay
        setTimeout(() => {
            isTurnInProgress = false;
            disableMoveButtons(false);
        }, 500);
    }
}

async function processMoveEvent(events, data) {
    // If a single event is passed, convert it to an array for consistency
    const eventList = Array.isArray(events) ? events : [events];
    
    // Process all non-faint events first
    for (const event of eventList) {
        if (event.type !== 'faint' && event.type !== 'fainted') {
            switch (event.type) {
                case 'move':
                    await handleMoveEvent(event, data);
                    break;
                case 'effectiveness':
                    handleEffectivenessEvent(event, data);
                    break;
                case 'status':
                    handleStatusEvent(event, data);
                    break;
                case 'status_change':
                    await handleStatusChangeEvent(event, data);
                    break;
                case 'priority_explanation':
                    handlePriorityExplanationEvent(event, data);
                    break;
                case 'priority_counter_success':
                    handlePriorityCounterSuccessEvent(event, data);
                    break;
                case 'priority_counter_failure':
                    handlePriorityCounterFailureEvent(event, data);
                    break;
                default:
                    console.warn('Unknown event type:', event.type);
            }
            // Add a small delay between events for better readability
            await new Promise(resolve => setTimeout(resolve, 300));
        }
    }
    
    // Then process faint events if any
    for (const event of eventList) {
        if (event.type === 'faint' || event.type === 'fainted') {
            const battleOver = await handleFaintEvent(event, data);
            if (battleOver) return true; // End processing if battle is over
        }
    }
    
    return false; // Battle continues
}

async function handleMoveEvent(event, data) {
    console.log('=== HANDLE MOVE EVENT ===');
    console.log('Event:', JSON.parse(JSON.stringify(event)));
    console.log('Event type:', event.type);
    
    const isPlayer = event.is_player;
    const attacker = event.attacker_name ? capitalize(event.attacker_name) : 
                     (isPlayer ? data.player_name : `Opponent ${data.opponent_name}`);
    
    // Log the full event for debugging
    console.log('Full event object:', JSON.stringify(event, null, 2));
    
    // Check if this is a status skip (Pokemon prevented from moving due to status)
    // This should only trigger for prevention messages, not status application messages
    const isStatusSkip = event.damage === 0 && 
                        event.status_message && 
                        (event.status_message.toLowerCase().includes('can\'t move!') || 
                         event.status_message.toLowerCase().includes('fast asleep.') ||
                         event.status_message.toLowerCase().includes('frozen solid!'));
    
    console.log('Status skip check:', {
        damage: event.damage,
        hasStatusMessage: !!event.status_message,
        message: event.status_message,
        isStatusSkip: isStatusSkip
    });
    
    if (isStatusSkip) {
        // Only show the status prevention message, not the move message
        console.log('Adding status skip message:', event.status_message);
        addLogMessage(event.status_message, false, isPlayer);
        return; // Skip the rest of the move handling
    }
    
    // If we get here, it's a normal move
    const moveMessage = `${attacker} used ${event.move}!`;
    console.log('Adding move message:', moveMessage);
    addLogMessage(moveMessage, false, isPlayer);
    
    // Execute attack animation
    await new Promise(resolve => setTimeout(resolve, 300));
    animateAttack(isPlayer);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Update HP based on the move's damage or healing
    if (event.damage > 0) {
        // Damaging move - update defender's HP
        if (isPlayer) {
            // Player attacked opponent
            data.opponent_hp = event.defender_hp;
            console.log(`Updating opponent HP: ${data.opponent_hp}/${data.opponent_max_hp}`);
            updateHealthBar('#opponent-health-bar', data.opponent_hp, data.opponent_max_hp);
        } else {
            // Opponent attacked player
            data.player_hp = event.defender_hp;
            console.log(`Updating player HP: ${data.player_hp}/${data.player_max_hp}`);
            updateHealthBar('#player-health-bar', data.player_hp, data.player_max_hp);
        }
    }
    
    // Also check for healing moves (attacker's HP may have changed)
    if (event.attacker_hp !== undefined) {
        if (isPlayer) {
            // Check if player's HP changed (healing move)
            if (data.player_hp !== event.attacker_hp) {
                data.player_hp = event.attacker_hp;
                console.log(`Updating player HP (healing): ${data.player_hp}/${data.player_max_hp}`);
                updateHealthBar('#player-health-bar', data.player_hp, data.player_max_hp);
            }
        } else {
            // Check if opponent's HP changed (healing move)
            if (data.opponent_hp !== event.attacker_hp) {
                data.opponent_hp = event.attacker_hp;
                console.log(`Updating opponent HP (healing): ${data.opponent_hp}/${data.opponent_max_hp}`);
                updateHealthBar('#opponent-health-bar', data.opponent_hp, data.opponent_max_hp);
            }
        }
    }
    
    // If there's a status message (not related to paralysis), show it
    if (event.status_message) {
        console.log('Adding status message:', event.status_message);
        await new Promise(resolve => setTimeout(resolve, 300));
        addLogMessage(event.status_message, false, isPlayer);
    } else {
        console.log('No status message in this event');
    }
    
    console.log('=== END HANDLE MOVE EVENT ===');
    return false; // Continue processing events
}

function handleEffectivenessEvent(event, data) {
    // Skip effectiveness messages that just repeat the move name
    if (event.message && !event.message.toLowerCase().includes('used')) {
        console.log('Adding effectiveness message:', event.message);
        addLogMessage(event.message, true, event.is_player);
    } else if (event.message) {
        console.log('Skipping duplicate move message:', event.message);
    }
}

function handleStatusEvent(event, data) {
    console.log('=== HANDLE STATUS EVENT ===');
    console.log('Status event:', JSON.parse(JSON.stringify(event)));
    
    // Display the status message
    if (event.message) {
        console.log('Adding status message:', event.message);
        const isPlayer = event.target === 'player';
        addLogMessage(event.message, false, isPlayer);
    } else {
        console.warn('Status event has no message:', event);
    }
    
    console.log('=== END HANDLE STATUS EVENT ===');
}

async function handleStatusChangeEvent(event, data) {
    console.log('=== HANDLE STATUS CHANGE EVENT ===');
    console.log('Status change event:', JSON.parse(JSON.stringify(event)));
    
    const pokemonType = event.pokemon; // 'player' or 'opponent'
    const eventType = event.event_type; // 'status_applied' or 'status_removed'
    const statusType = event.status_type; // e.g., 'sleep', 'burn', etc.
    const statusName = event.status_name; // e.g., 'Sleep', 'Burn', etc.
    const pokemonName = event.pokemon_name;
    
    console.log(`Processing ${eventType} for ${pokemonType}: ${statusType} (${statusName})`);
    
    if (eventType === 'status_applied') {
        // Add visual feedback for status application
        console.log(`Adding status indicator for ${statusType} on ${pokemonType}`);
        
        // Create status object for the indicator
        const statusObj = {
            type: statusType,
            name: statusName,
            is_major: true, // Assume major for visual purposes
            duration: -1,
            counter: 0
        };
        
        // Add the status indicator with animation
        addStatusIndicator(pokemonType, statusObj);
        
        // Add visual notification (optional - could be a brief animation or effect)
        await addStatusChangeNotification(pokemonType, statusName, 'applied');
        
    } else if (eventType === 'status_removed') {
        // Remove status indicator with animation
        console.log(`Removing status indicator for ${statusType} from ${pokemonType}`);
        
        try {
            await removeStatusIndicator(pokemonType, statusType);
            console.log(`✅ Successfully removed ${statusType} indicator from ${pokemonType}`);
        } catch (error) {
            console.error(`Error removing ${statusType} indicator from ${pokemonType}:`, error);
        }
        
        // Add visual notification for status removal
        await addStatusChangeNotification(pokemonType, statusName, 'removed');
    }
    
    console.log('=== END HANDLE STATUS CHANGE EVENT ===');
}

async function addStatusChangeNotification(pokemonType, statusName, changeType) {
    console.log(`Adding status change notification: ${statusName} ${changeType} for ${pokemonType}`);
    
    // Get the Pokemon element to show the notification near
    const pokemonElement = document.getElementById(pokemonType);
    if (!pokemonElement) {
        console.warn(`Pokemon element not found for ${pokemonType}`);
        return;
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `status-change-notification ${changeType}`;
    notification.textContent = changeType === 'applied' ? `+${statusName}` : `-${statusName}`;
    
    // Position the notification near the Pokemon
    const pokemonRect = pokemonElement.getBoundingClientRect();
    notification.style.position = 'absolute';
    notification.style.left = `${pokemonRect.left + pokemonRect.width / 2}px`;
    notification.style.top = `${pokemonRect.top - 20}px`;
    notification.style.transform = 'translateX(-50%)';
    notification.style.zIndex = '1000';
    notification.style.pointerEvents = 'none';
    notification.style.fontSize = '14px';
    notification.style.fontWeight = 'bold';
    notification.style.padding = '4px 8px';
    notification.style.borderRadius = '4px';
    notification.style.color = 'white';
    notification.style.textShadow = '1px 1px 2px rgba(0,0,0,0.8)';
    
    // Set color based on change type
    if (changeType === 'applied') {
        notification.style.backgroundColor = 'rgba(231, 76, 60, 0.9)'; // Red for status applied
    } else {
        notification.style.backgroundColor = 'rgba(46, 204, 113, 0.9)'; // Green for status removed
    }
    
    // Add to document
    document.body.appendChild(notification);
    
    // Animate the notification
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(-50%) translateY(10px)';
    
    // Fade in and move up
    setTimeout(() => {
        notification.style.transition = 'all 0.3s ease-out';
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(-50%) translateY(-10px)';
    }, 10);
    
    // Fade out and remove after delay
    setTimeout(() => {
        notification.style.transition = 'all 0.3s ease-in';
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(-50%) translateY(-30px)';
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 1500);
    
    // Add a small delay for the animation
    await new Promise(resolve => setTimeout(resolve, 200));
}

async function handleFaintEvent(event, data) {
    const pokemonName = capitalize(event.pokemon_name);
    const isPlayer = event.is_player;
    
    // Update HP bar to 0
    if (isPlayer) {
        data.player_hp = 0;
        updateHealthBar('#player-health-bar', 0, data.player_max_hp);
        // Player fainted - show player's Pokémon fainting
        await animateFaint(true);
    } else {
        data.opponent_hp = 0;
        updateHealthBar('#opponent-health-bar', 0, data.opponent_max_hp);
        // Opponent fainted - show opponent's Pokémon fainting
        await animateFaint(false);
    }
    
    // Show faint message with correct Pokémon name
    addLogMessage(`${pokemonName} fainted!`);
    
    // Add a small delay before showing the battle result
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Show the battle result message (win/loss)
    if (isPlayer) {
        addLogMessage("You were defeated!");
    } else {
        addLogMessage("You won the battle!");
    }
    
    // Add a small delay before redirecting
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Check for game over URL
    if (data.game_over_url) {
        window.location.href = data.game_over_url;
    }
    
    return true; // Battle is over
}

// Old functions removed as they're no longer needed
// processPlayerMove and processOpponentMove have been replaced by processMoveEvent

// Function to forfeit the battle
function forfeitBattle() {
    // Prevent forfeit if battle hasn't started or a turn is in progress
    if (!battleStarted || isTurnInProgress) return;
    
    // Confirm forfeit
    if (confirm("Are you sure you want to forfeit the battle?")) {
        // Add message to battle log
        addLogMessage("You forfeited the battle!", false, true);
        
        // Wait a moment before redirecting
        setTimeout(() => {
            // Redirect to game over page
            window.location.href = "/game_over?result=forfeit";
        }, 2000);
    }
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function handleTypeIconError(imgElement, moveType) {
    console.warn('Could not load image for type:', moveType);
    imgElement.onerror = null; // Prevent infinite loop
    imgElement.src = '/static/images/type/normal.png'; // Set to default normal type icon
}

// Priority system functions
function displayPriorityValues() {
    console.log('Displaying priority values for moves...');
    
    const moveButtons = document.querySelectorAll('.move-button');
    console.log(`Found ${moveButtons.length} move buttons`);
    
    moveButtons.forEach((button, index) => {
        const priority = parseInt(button.getAttribute('data-priority') || '0');
        const isPriorityCounter = button.getAttribute('data-is-priority-counter') === 'True';
        const moveName = button.querySelector('.move-name')?.textContent || 'Unknown';
        
        console.log(`Move ${index + 1}: ${moveName}, Priority: ${priority}, Counter: ${isPriorityCounter}`);
        
        // Check if priority indicators exist in the HTML
        const priorityIndicator = button.querySelector('.priority-indicator');
        const counterIndicator = button.querySelector('.priority-counter-indicator');
        
        console.log(`  - Priority indicator found: ${!!priorityIndicator}`);
        console.log(`  - Counter indicator found: ${!!counterIndicator}`);
        
        // Priority indicators should already be visible from the HTML template
        // No need to modify them here
    });
}

function showTurnOrderPreview(playerMoveName) {
    console.log(`Showing turn order preview for player move: ${playerMoveName}`);
    
    const turnOrderPreview = document.getElementById('turn-order-preview');
    const turnOrderText = document.getElementById('turn-order-text');
    
    if (!turnOrderPreview || !turnOrderText) {
        console.error('Turn order preview elements not found');
        return;
    }
    
    // Get player move data
    const playerMoveButton = Array.from(document.querySelectorAll('.move-button')).find(button => 
        button.querySelector('.move-name').textContent.toLowerCase() === playerMoveName.toLowerCase()
    );
    
    if (!playerMoveButton) {
        console.error(`Player move button not found for: ${playerMoveName}`);
        return;
    }
    
    const playerPriority = parseInt(playerMoveButton.getAttribute('data-priority') || '0');
    const playerIsPriorityCounter = playerMoveButton.getAttribute('data-is-priority-counter') === 'True';
    
    // For now, assume opponent uses a normal priority move (priority 0)
    // In a real implementation, this would come from the server or AI decision
    const opponentPriority = 0;
    const opponentIsPriorityCounter = false;
    
    // Get Pokemon names
    const playerName = document.getElementById('player-pokemon-name').textContent;
    const opponentName = document.getElementById('opponent-pokemon-name').textContent;
    
    // Calculate turn order and explanation
    let firstPokemon, secondPokemon;
    let firstMove, secondMove;
    let explanation = "";
    
    // Handle priority counters first
    if (playerIsPriorityCounter) {
        firstPokemon = playerName;
        secondPokemon = opponentName;
        firstMove = playerMoveName;
        secondMove = "opponent's move";
        explanation = " (Priority Counter - may intercept)";
    } else if (playerPriority > opponentPriority) {
        firstPokemon = playerName;
        secondPokemon = opponentName;
        firstMove = playerMoveName;
        secondMove = "opponent's move";
        explanation = ` (Priority +${playerPriority})`;
    } else if (opponentPriority > playerPriority) {
        firstPokemon = opponentName;
        secondPokemon = playerName;
        firstMove = "opponent's move";
        secondMove = playerMoveName;
        if (playerPriority < 0) {
            explanation = ` (${playerMoveName} has negative priority ${playerPriority})`;
        } else {
            explanation = " (Opponent has higher priority)";
        }
    } else {
        // Same priority - would depend on speed
        firstPokemon = playerName;
        secondPokemon = opponentName;
        firstMove = playerMoveName;
        secondMove = "opponent's move";
        if (playerPriority === 0) {
            explanation = " (Speed determines order)";
        } else {
            explanation = ` (Both priority ${playerPriority >= 0 ? '+' + playerPriority : playerPriority}, speed determines order)`;
        }
    }
    
    // Update the preview text with priority explanation
    turnOrderText.innerHTML = `
        <div class="turn-order-main">
            <span class="turn-order-item first">${firstPokemon}: ${firstMove}</span> → 
            <span class="turn-order-item second">${secondPokemon}: ${secondMove}</span>
        </div>
        <div class="turn-order-explanation">${explanation}</div>
    `;
    
    // Show the preview
    turnOrderPreview.classList.remove('hidden');
    
    console.log(`Turn order preview shown: ${firstPokemon} (${firstMove}) → ${secondPokemon} (${secondMove})`);
}

function hideTurnOrderPreview() {
    const turnOrderPreview = document.getElementById('turn-order-preview');
    if (turnOrderPreview) {
        turnOrderPreview.classList.add('hidden');
    }
}

function updateMoveButtonInteractions() {
    console.log('Setting up move button interactions for priority display...');
    
    const moveButtons = document.querySelectorAll('.move-button');
    moveButtons.forEach(button => {
        const moveName = button.querySelector('.move-name').textContent;
        
        // Add hover effect to show turn order preview (non-intrusive)
        button.addEventListener('mouseenter', () => {
            if (!isTurnInProgress && battleStarted) {
                showTurnOrderPreview(moveName);
            }
        });
        
        // Hide preview when mouse leaves
        button.addEventListener('mouseleave', () => {
            if (!isTurnInProgress) {
                hideTurnOrderPreview();
            }
        });
        
        // Don't modify the original onclick functionality
        // Just add a non-intrusive click listener for preview
        button.addEventListener('click', () => {
            if (!isTurnInProgress && battleStarted) {
                selectedMove = moveName;
                showTurnOrderPreview(moveName);
            }
        });
    });
}

// Function to add priority-specific battle messages
function addPriorityBattleMessage(message, isPriorityRelated = false) {
    console.log(`Adding priority battle message: ${message}`);
    
    // Add to battle log with special styling for priority messages
    const battleLogText = document.getElementById('battle-log-text');
    if (battleLogText) {
        if (isPriorityRelated) {
            battleLogText.innerHTML = `<span style="color: #f1c40f;">⚡ ${message}</span>`;
        } else {
            battleLogText.textContent = message;
        }
    }
    
    // Also add to the right-side battle log
    const rightBattleLog = document.getElementById('right-battle-log');
    if (rightBattleLog) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        if (isPriorityRelated) {
            logEntry.classList.add('priority-message');
            logEntry.innerHTML = `⚡ ${message}`;
            logEntry.style.color = '#f1c40f';
            logEntry.style.borderLeftColor = '#f1c40f';
        } else {
            logEntry.textContent = message;
        }
        
        rightBattleLog.querySelector('div').appendChild(logEntry);
        rightBattleLog.scrollTop = rightBattleLog.scrollHeight;
    }
}

// Priority-specific event handlers

function handlePriorityExplanationEvent(event, data) {
    console.log('=== HANDLE PRIORITY EXPLANATION EVENT ===');
    console.log('Event:', event);
    
    // Add priority explanation message with special styling
    addLogMessage(event.message, false, null, true); // true for isPriorityRelated
    
    console.log('Priority explanation message added:', event.message);
}

function handlePriorityCounterSuccessEvent(event, data) {
    console.log('=== HANDLE PRIORITY COUNTER SUCCESS EVENT ===');
    console.log('Event:', event);
    
    const isPlayer = event.target === 'player';
    
    // Add priority counter success message with special styling
    addLogMessage(event.message, false, isPlayer, true); // true for isPriorityRelated
    
    console.log('Priority counter success message added:', event.message);
}

function handlePriorityCounterFailureEvent(event, data) {
    console.log('=== HANDLE PRIORITY COUNTER FAILURE EVENT ===');
    console.log('Event:', event);
    
    const isPlayer = event.target === 'player';
    
    // Add priority counter failure message with special styling
    addLogMessage(event.message, false, isPlayer, true); // true for isPriorityRelated
    
    console.log('Priority counter failure message added:', event.message);
}