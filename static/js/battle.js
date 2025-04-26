function updateHealthBar(elementId, currentHp, maxHp) {
    const healthBar = document.getElementById(elementId);
    const healthPercentage = (currentHp / maxHp) * 100;
    healthBar.style.width = healthPercentage + '%';
    if (healthPercentage > 50) {
        healthBar.style.backgroundColor = 'green';
    } else if (healthPercentage > 20) {
        healthBar.style.backgroundColor = 'yellow';
    } else {
        healthBar.style.backgroundColor = 'red';
    }
}

async function makeMove(move) {
    const response = await fetch('/move', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ move: move })
    });

    if (response.redirected) {
        // Redirect to the game over screen if the server indicates the game is over
        window.location.href = response.url;
    } else {
        const data = await response.json();
        if (response.ok) {
            document.getElementById("player-hp-text").innerText = `Player HP: ${data.player_hp}`;
            document.getElementById("opponent-hp-text").innerText = `Opponent HP: ${data.opponent_hp}`;
            updateHealthBar('player-health-bar', data.player_hp, data.player_max_hp);
            updateHealthBar('opponent-health-bar', data.opponent_hp, data.opponent_max_hp);

            document.getElementById('hit-sound').play();
            document.querySelector(".opponent-pokemon").classList.add('shake');
            setTimeout(() => document.querySelector(".opponent-pokemon").classList.remove('shake'), 500);

            const logElement = document.getElementById("battle-log");
            logElement.innerHTML = '';
            data.battle_log.forEach(log => {
                const li = document.createElement("li");
                li.textContent = log;
                logElement.appendChild(li);
            });
        } else {
            alert(data.error);
        }
    }
}