// Global variables to track game state
let isTurnInProgress = false;
let battleLogEl;

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
});

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
    const ul = battleLogEl.querySelector("ul");
    const li = document.createElement("li");
    li.textContent = message;
    li.className = "py-1 border-b border-gray-700";
    ul.appendChild(li);
    
    // Auto-scroll to the bottom
    battleLogEl.scrollTop = battleLogEl.scrollHeight;
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

// New function to animate a Pokémon fainting
function animateFaint(isPlayer) {
    const pokemonElement = isPlayer ? 
        document.getElementById("player") : 
        document.getElementById("opponent");
    
    // Add the faint animation class
    pokemonElement.classList.add('faint-animation');
    
    // Play a faint sound if available
    if (document.getElementById('faint-sound')) {
        document.getElementById('faint-sound').play();
    }
    
    // Return a promise that resolves when the animation is complete
    return new Promise(resolve => {
        setTimeout(() => {
            resolve();
        }, 1500); // Animation takes 1.5 seconds
    });
}

async function makeMove(move) {
    // Prevent multiple moves during a turn
    if (isTurnInProgress) return;
    
    isTurnInProgress = true;
    disableMoveButtons(true);
    
    try {
        // Player's turn - log the move
        addLogMessage(`You used ${move}!`);
        
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
        
        // Execute player's attack animation
        animateAttack(true);
        
        // Wait for animation to complete
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Update opponent's HP to show the damage from player's move
        document.getElementById("opponent-hp-text").innerText = `Opponent HP: ${data.opponent_hp}`;
        updateHealthBar('opponent-health-bar', data.opponent_hp, data.opponent_max_hp);
        
        // Check if opponent is defeated
        if (data.opponent_hp <= 0) {
            // Show HP as 0 explicitly
            document.getElementById("opponent-hp-text").innerText = `Opponent HP: 0`;
            updateHealthBar('opponent-health-bar', 0, data.opponent_max_hp);
            
            // Add faint message to battle log
            addLogMessage("The opponent's Pokémon fainted!");
            
            // Play the faint animation
            await animateFaint(false);
            
            // Redirect to game over after animation completes
            if (data.game_over_url) {
                window.location.href = data.game_over_url;
            }
            return;
        }
        
        // Wait before opponent's turn
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Opponent's turn
        if (data.opponent_move) {
            addLogMessage(`Opponent used ${data.opponent_move}!`);
            
            // Execute opponent's attack animation
            animateAttack(false);
            
            // Wait for animation to complete
            await new Promise(resolve => setTimeout(resolve, 800));
            
            // Update player's HP to show damage from opponent's move
            document.getElementById("player-hp-text").innerText = `Player HP: ${data.player_hp}`;
            updateHealthBar('player-health-bar', data.player_hp, data.player_max_hp);
            
            // Check if player is defeated
            if (data.player_hp <= 0) {
                // Show HP as 0 explicitly
                document.getElementById("player-hp-text").innerText = `Player HP: 0`;
                updateHealthBar('player-health-bar', 0, data.player_max_hp);
                
                // Add faint message to battle log
                addLogMessage("Your Pokémon fainted!");
                
                // Play the faint animation
                await animateFaint(true);
                
                // Redirect to game over after animation completes
                if (data.game_over_url) {
                    window.location.href = data.game_over_url;
                }
                return;
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