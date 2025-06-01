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
    const hpTextElement = document.getElementById(selector.replace('-health-bar', '-hp'));
    if (hpTextElement) {
        hpTextElement.textContent = `${Math.round(currentHp)}/${maxHp}`;
    }
    
    console.log(`Updated ${selector} to ${healthPercentage.toFixed(1)}% (${currentHp}/${maxHp})`);
}

function addLogMessage(message) {
    // Update the battle log in the original location (for compatibility)
    const ul = battleLogEl.querySelector("ul");
    const li = document.createElement("li");
    li.textContent = message;
    li.className = "py-1 border-b border-gray-700";
    ul.appendChild(li);
    
    // Auto-scroll to the bottom
    battleLogEl.scrollTop = battleLogEl.scrollHeight;
    
    // Update the battle log text in the new battle controls panel
    const battleLogText = document.getElementById("battle-log-text");
    if (battleLogText) {
        battleLogText.textContent = message;
    }
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

// Function to animate a Pokémon fainting with distorted cry
async function animateFaint(isPlayer) {
    const pokemonElement = isPlayer ? 
        document.getElementById("player") : 
        document.getElementById("opponent");
    
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
    
    // Return a promise that resolves when the animation is complete
    return new Promise(resolve => {
        setTimeout(() => {
            resolve();
        }, 1500); // Animation takes 1.5 seconds
    });
}

async function makeMove(move) {
    // Prevent moves if battle hasn't started or a turn is in progress
    if (!battleStarted || isTurnInProgress) return;
    
    isTurnInProgress = true;
    disableMoveButtons(true);
    
    // Update PP display
    updateMovePP(move, -1); // Will be updated with actual PP from server
    
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
        
        // Process turns in the correct order based on speed
        if (turn_info.player_first) {
            // Player moves first if they have HP left
            if (data.player_hp > 0) {
                await processPlayerMove(playerPokemonName, opponentPokemonName, move, data, turn_info);
                if (data.is_game_over) return;
            }
            
            // Opponent moves second if they have HP left
            if (data.opponent_hp > 0) {
                await processOpponentMove(playerPokemonName, opponentPokemonName, data, turn_info);
                if (data.is_game_over) return;
            }
        } else {
            // Opponent moves first if they have HP left
            if (data.opponent_hp > 0) {
                await processOpponentMove(playerPokemonName, opponentPokemonName, data, turn_info);
                if (data.is_game_over) return;
            }
            
            // Player moves second if they have HP left
            if (data.player_hp > 0) {
                await processPlayerMove(playerPokemonName, opponentPokemonName, move, data, turn_info);
                if (data.is_game_over) return;
            }
        }
        
    } finally {
        // Turn complete - re-enable buttons after a short delay
        setTimeout(() => {
            isTurnInProgress = false;
            disableMoveButtons(false);
        }, 500);
    }
}

async function processPlayerMove(playerName, opponentName, move, data, turnInfo) {
    // Log player's move
    addLogMessage(`${capitalize(playerName)} used ${move}!`);
    
    // Show effectiveness messages for player's move if any
    if (turnInfo.effectiveness_messages && turnInfo.effectiveness_messages.length > 0) {
        // Since we process moves in order, the player's move's effectiveness message
        // will be the first one if they moved first, or the second one if they moved second
        const playerMoveIndex = turnInfo.player_first ? 0 : 1;
        
        // Only show the message if it exists and is for the player's move
        if (turnInfo.effectiveness_messages[playerMoveIndex]) {
            const message = turnInfo.effectiveness_messages[playerMoveIndex];
            if (message.includes('It\'s super effective!') || 
                message.includes('It\'s not very effective...') ||
                message.includes('It had no effect...')) {
                await new Promise(resolve => setTimeout(resolve, 500));
                addLogMessage(message);
            }
        }
    }
    
    // Execute player's attack animation
    await new Promise(resolve => setTimeout(resolve, 300));
    animateAttack(true);
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Update opponent's HP
    const opponentHp = Math.max(0, data.opponent_hp);
    updateHealthBar('#opponent-health-bar', opponentHp, data.opponent_max_hp);
    
    // Check if opponent is defeated
    if (opponentHp <= 0) {
        updateHealthBar('#opponent-health-bar', 0, data.opponent_max_hp);
        addLogMessage(`Opponent ${capitalize(opponentName)} fainted!`);
        await animateFaint(false);
        addLogMessage("You won the battle!");
        await new Promise(resolve => setTimeout(resolve, 2000));
        if (data.game_over_url) {
            window.location.href = data.game_over_url;
        }
        return true; // Battle is over
    }
    return false; // Battle continues
}

async function processOpponentMove(playerName, opponentName, data, turnInfo) {
    // Determine opponent's move
    const move = turnInfo.opponent_move;
    
    // Log opponent's move
    addLogMessage(`Opponent ${capitalize(opponentName)} used ${move}!`);
    
    // Show effectiveness messages for opponent's move if any
    if (turnInfo.effectiveness_messages && turnInfo.effectiveness_messages.length > 0) {
        // Since we process moves in order, the opponent's move's effectiveness message
        // will be the first one if they moved first, or the second one if they moved second
        const opponentMoveIndex = turnInfo.player_first ? 1 : 0;
        
        // Only show the message if it exists and is for the opponent's move
        if (turnInfo.effectiveness_messages[opponentMoveIndex]) {
            const message = turnInfo.effectiveness_messages[opponentMoveIndex];
            if (message.includes('It\'s super effective!') || 
                message.includes('It\'s not very effective...') ||
                message.includes('It had no effect...')) {
                await new Promise(resolve => setTimeout(resolve, 500));
                addLogMessage(message);
            }
        }
    }
    
    // Execute opponent's attack animation
    await new Promise(resolve => setTimeout(resolve, 300));
    animateAttack(false);
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Update player's HP
    const playerHp = Math.max(0, data.player_hp);
    updateHealthBar('#player-health-bar', playerHp, data.player_max_hp);
    
    // Check if player is defeated
    if (playerHp <= 0) {
        updateHealthBar('#player-health-bar', 0, data.player_max_hp);
        addLogMessage(`${capitalize(playerName)} fainted!`);
        await animateFaint(true);
        addLogMessage("You were defeated!");
        await new Promise(resolve => setTimeout(resolve, 2000));
        if (data.game_over_url) {
            window.location.href = data.game_over_url;
        }
        return true; // Battle is over
    }
    return false; // Battle continues
}

// Function to forfeit the battle
function forfeitBattle() {
    // Prevent forfeit if battle hasn't started or a turn is in progress
    if (!battleStarted || isTurnInProgress) return;
    
    // Confirm forfeit
    if (confirm("Are you sure you want to forfeit the battle?")) {
        // Add message to battle log
        addLogMessage("You forfeited the battle!");
        
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