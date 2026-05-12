#!/usr/bin/env node

const fs = require('fs');
const {Generations, Pokemon, Move, Field, calculate} = require('@smogon/calc');

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const gen = Generations.get(input.gen || 9);

const attacker = new Pokemon(gen, input.attacker.species, {
  level: input.attacker.level || 100,
  ability: input.attacker.ability,
  item: input.attacker.item,
  nature: input.attacker.nature,
  evs: input.attacker.evs,
  ivs: input.attacker.ivs,
  boosts: input.attacker.boosts,
  status: input.attacker.status,
});

const defender = new Pokemon(gen, input.defender.species, {
  level: input.defender.level || 100,
  ability: input.defender.ability,
  item: input.defender.item,
  nature: input.defender.nature,
  evs: input.defender.evs,
  ivs: input.defender.ivs,
  boosts: input.defender.boosts,
  status: input.defender.status,
});

const move = new Move(gen, input.move.name, {
  ability: input.attacker.ability,
  item: input.attacker.item,
});

const field = new Field({
  weather: input.field && input.field.weather,
  terrain: input.field && input.field.terrain,
  isReflect: input.field && input.field.isReflect,
  isLightScreen: input.field && input.field.isLightScreen,
  isAuroraVeil: input.field && input.field.isAuroraVeil,
});

const result = calculate(gen, attacker, defender, move, field);
const damage = Array.isArray(result.damage) ? result.damage.flat(Infinity) : [result.damage];

process.stdout.write(JSON.stringify({
  damage,
  min: Math.min(...damage),
  max: Math.max(...damage),
  description: result.desc && result.desc(),
}) + '\n');
