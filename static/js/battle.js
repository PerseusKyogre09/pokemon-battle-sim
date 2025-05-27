// Global variables to track game state
let isTurnInProgress = false;
let battleLogEl;
let battleStarted = false; // Set to false initially until animation completes

// Initialize the battle when the page loads
document.addEventListener('DOMContentLoaded', function() {
    battleLogEl = document.getElementById("battle-log");
    
    // Start with an empty battle log
    addLogMessage("Battle started! Choose your move.");
    
    // Set initial health bars
    const playerHealthText = document.getElementById("player-hp-text").innerText;
    const opponentHealthText = document.getElementById("opponent-hp-text").innerText;
    
    const playerHp = parseInt(playerHealthText.match(/\d+/)[0]);
    const opponentHp = parseInt(opponentHealthText.match(/\d+/)[0]);
    
    updateHealthBar('player-health-bar', playerHp, playerHp);
    updateHealthBar('opponent-health-bar', opponentHp, opponentHp);
    
    // Hide Pokémon and health bars initially
    const playerPokemon = document.getElementById('player');
    const opponentPokemon = document.getElementById('opponent');
    const playerHealthContainer = document.getElementById('player-health-container');
    const opponentHealthContainer = document.getElementById('opponent-health-container');
    const moveButtons = document.querySelectorAll('.move-button');
    
    playerPokemon.classList.add('hidden-element');
    opponentPokemon.classList.add('hidden-element');
    playerHealthContainer.classList.add('hidden-element');
    opponentHealthContainer.classList.add('hidden-element');
    
    // Disable move buttons until animation completes
    moveButtons.forEach(button => {
        button.disabled = true;
        button.style.opacity = 0.5;
    });
    
    // Start the battle sequence with animations
    startBattleSequence();
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

// Start the battle sequence with animations - not used by default but kept for future use
async function startBattleSequence() {
    // Start battle music
    const battleMusic = document.getElementById('battle-music');
    battleMusic.volume = 0.7;
    battleMusic.play();
    
    // Wait a moment before starting animations
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Show the pokeballs
    const playerPokeball = document.getElementById('player-pokeball');
    const opponentPokeball = document.getElementById('opponent-pokeball');
    
    playerPokeball.classList.remove('hidden-element');
    opponentPokeball.classList.remove('hidden-element');
    
    // Get the Pokémon elements
    const playerPokemon = document.getElementById('player');
    const opponentPokemon = document.getElementById('opponent');
    
    // Get the flash element
    const flashElement = document.getElementById('flash-element');
    
    // Get the health containers
    const playerHealthContainer = document.getElementById('player-health-container');
    const opponentHealthContainer = document.getElementById('opponent-health-container');
    
    // Get the Pokémon data from the audio elements
    const playerCry = document.getElementById('player-cry');
    const opponentCry = document.getElementById('opponent-cry');
    const playerPokemonName = playerCry.getAttribute('data-pokemon');
    const opponentPokemonName = opponentCry.getAttribute('data-pokemon');
    
    // Load the Pokémon cries
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Play the Pokéball throw sound for opponent's Pokémon
    const pokeballSound = document.getElementById('pokeball-sound');
    pokeballSound.play();
    
    // Animate opponent's Pokéball throw
    opponentPokeball.classList.add('throw-animation-opponent');
    
    // Wait for the throw animation to complete
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Flash the screen
    flashElement.classList.add('flash');
    
    // Wait for the flash
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Hide the opponent's Pokéball and show the Pokémon
    opponentPokeball.classList.add('hidden-element');
    opponentPokemon.classList.remove('hidden-element');
    
    // Play opponent's Pokémon cry
    loadPokemonCry(opponentCry, opponentPokemonName);
    
    // Show opponent's health bar
    await new Promise(resolve => setTimeout(resolve, 500));
    opponentHealthContainer.classList.remove('hidden-element');
    
    // Wait a moment before player's turn
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Play the Pokéball throw sound for player's Pokémon
    pokeballSound.currentTime = 0;
    pokeballSound.play();
    
    // Animate player's Pokéball throw
    playerPokeball.classList.add('throw-animation-player');
    
    // Wait for the throw animation to complete
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Flash the screen again
    flashElement.classList.remove('flash');
    await new Promise(resolve => setTimeout(resolve, 50));
    flashElement.classList.add('flash');
    
    // Wait for the flash
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Hide the player's Pokéball and show the Pokémon
    playerPokeball.classList.add('hidden-element');
    playerPokemon.classList.remove('hidden-element');
    
    // Play player's Pokémon cry
    loadPokemonCry(playerCry, playerPokemonName);
    
    // Show player's health bar
    await new Promise(resolve => setTimeout(resolve, 500));
    playerHealthContainer.classList.remove('hidden-element');
    
    // Remove the flash
    flashElement.classList.remove('flash');
    
    // Enable move buttons with fade-in effect
    const moveButtons = document.querySelectorAll('.move-button');
    moveButtons.forEach(button => {
        button.disabled = false;
        button.style.transition = 'opacity 0.5s ease-in';
        button.style.opacity = 1;
    });
    
    // Set battle as started
    battleStarted = true;
}

function updateHealthBar(elementId, currentHp, maxHp) {
    const healthBar = document.getElementById(elementId);
    const healthPercentage = (currentHp / maxHp) * 100;
    healthBar.style.width = healthPercentage + '%';
    
    // Update health bar color based on percentage
    if (healthPercentage > 50) {
        healthBar.style.backgroundColor = '#10B981'; // Tailwind green-500
    } else if (healthPercentage > 20) {
        healthBar.style.backgroundColor = '#FBBF24'; // Tailwind yellow-400
    } else {
        healthBar.style.backgroundColor = '#EF4444'; // Tailwind red-500
    }
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
            button.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            button.classList.remove('opacity-50', 'cursor-not-allowed');
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
        
        const { turn_info } = data;
        
        // Process turns in the correct order based on speed
        if (turn_info.player_first) {
            // Player moves first
            await processPlayerMove(playerPokemonName, opponentPokemonName, move, data, turn_info);
            if (data.is_game_over) return;
            
            // Opponent moves second if they have HP left
            if (turn_info.opponent_damage > 0) {
                await processOpponentMove(playerPokemonName, opponentPokemonName, data, turn_info);
                if (data.player_hp <= 0) return;
            }
        } else {
            // Opponent moves first
            if (turn_info.opponent_damage > 0) {
                await processOpponentMove(playerPokemonName, opponentPokemonName, data, turn_info);
                if (data.player_hp <= 0) return;
            }
            
            // Player moves second if they have HP left
            await processPlayerMove(playerPokemonName, opponentPokemonName, move, data, turn_info);
            if (data.is_game_over) return;
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
    
    // Execute player's attack animation
    animateAttack(true);
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Update opponent's HP
    document.getElementById("opponent-hp-text").innerText = `Opponent ${capitalize(opponentName)} HP: ${data.opponent_hp}`;
    updateHealthBar('opponent-health-bar', data.opponent_hp, data.opponent_max_hp);
    
    // Check if opponent is defeated
    if (data.opponent_hp <= 0) {
        document.getElementById("opponent-hp-text").innerText = `Opponent ${capitalize(opponentName)} HP: 0`;
        updateHealthBar('opponent-health-bar', 0, data.opponent_max_hp);
        addLogMessage(`Opponent ${capitalize(opponentName)} fainted!`);
        await animateFaint(false);
        addLogMessage("You won the battle!");
        await new Promise(resolve => setTimeout(resolve, 5000));
        if (data.game_over_url) {
            window.location.href = data.game_over_url;
        }
    }
}

async function processOpponentMove(playerName, opponentName, data, turnInfo) {
    // Log opponent's move
    addLogMessage(`Opponent ${capitalize(opponentName)} used ${turnInfo.opponent_move}!`);
    
    // Execute opponent's attack animation
    animateAttack(false);
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Update player's HP
    document.getElementById("player-hp-text").innerText = `${capitalize(playerName)} HP: ${data.player_hp}`;
    updateHealthBar('player-health-bar', data.player_hp, data.player_max_hp);
    
    // Check if player is defeated
    if (data.player_hp <= 0) {
        document.getElementById("player-hp-text").innerText = `${capitalize(playerName)} HP: 0`;
        updateHealthBar('player-health-bar', 0, data.player_max_hp);
        addLogMessage(`${capitalize(playerName)} fainted!`);
        await animateFaint(true);
        addLogMessage("You lost the battle!");
        await new Promise(resolve => setTimeout(resolve, 5000));
        if (data.game_over_url) {
            window.location.href = data.game_over_url;
        }
    }
}

// Function to use a potion to heal the player's Pokémon
function usePotion() {
    // Prevent using potion if battle hasn't started or a turn is in progress
    if (!battleStarted || isTurnInProgress) return;
    
    // Get current player HP
    const playerHpText = document.getElementById("player-hp-text").innerText;
    const currentHp = parseInt(playerHpText.match(/\d+/)[0]);
    
    // Get player max HP (this should be stored somewhere, for now we'll use 100)
    const maxHp = 100; // This should be replaced with the actual max HP
    
    // Don't use potion if HP is already full
    if (currentHp >= maxHp) {
        addLogMessage("Your Pokémon's HP is already full!");
        return;
    }
    
    // Calculate new HP (heal by 20 points, but don't exceed max)
    const healAmount = 20;
    const newHp = Math.min(currentHp + healAmount, maxHp);
    
    // Update HP display
    const playerPokemonName = document.getElementById('player-cry').getAttribute('data-pokemon');
    document.getElementById("player-hp-text").innerText = `${capitalize(playerPokemonName)} HP: ${newHp}`;
    updateHealthBar('player-health-bar', newHp, maxHp);
    
    // Add message to battle log
    addLogMessage(`You used a Potion! ${capitalize(playerPokemonName)} recovered ${newHp - currentHp} HP.`);
    
    // Play healing sound (if available)
    const healSound = document.getElementById('hit-sound');
    if (healSound) {
        healSound.play();
    }
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