import { gsap } from 'gsap';
import moveAnimationsData from './move_animations.json';

export const TYPE_COLORS: Record<string, string> = {
  Normal: "#A8A77A", Fire: "#EE8130", Water: "#6390F0", Electric: "#F7D02C",
  Grass: "#7AC74C", Ice: "#96D9D6", Fighting: "#C22E28", Poison: "#A33EA1",
  Ground: "#E2BF65", Flying: "#A98FF3", Psychic: "#F95587", Bug: "#A6B91A",
  Rock: "#B8A038", Ghost: "#735797", Dragon: "#6F35FC", Dark: "#705746",
  Steel: "#B7B7CE", Fairy: "#D685AD",
};

export const PARTICLE_CONFIG: Record<string, { path: string, count?: number, isAnimated?: boolean }> = {
  Fire: { path: "/images/particles/fire/", count: 4, isAnimated: true },
  Water: { path: "/images/particles/bubble_gba.png" },
  Electric: { path: "/images/particles/bolt_gba.png" },
  Grass: { path: "/images/particles/leaf_gba.png" },
  Fighting: { path: "/images/particles/slash_gba.png" },
  Normal: { path: "/images/particles/star_gba.png" },
  Default: { path: "/images/particles/star_gba.png" }
};

const preloadParticles = () => {
  if (typeof window === 'undefined') return;
  for(let i=1; i<=4; i++) new Image().src = `/images/particles/fire/${i}.png`;
  ['bubble_gba', 'bolt_gba', 'leaf_gba', 'slash_gba', 'star_gba', 'fight/kick'].forEach(name => {
    new Image().src = `/images/particles/${name}.png`;
  });
};
preloadParticles();

export const ActionAtoms = {
  physicalStrike: (attacker: HTMLElement, isPlayer: boolean) => {
    const tl = gsap.timeline();
    const xDist = isPlayer ? 140 : -140;
    const yDist = isPlayer ? -40 : 40;
    return tl.to(attacker, { x: xDist, y: yDist, duration: 0.12, ease: "power2.out" })
             .to(attacker, { x: 0, y: 0, duration: 0.3, ease: "back.out(1.7)" });
  },

  spawnGBAParticles: (sourceEl: HTMLElement, targetEl: HTMLElement, type: string, amount: number = 12) => {
    const config = PARTICLE_CONFIG[type] || PARTICLE_CONFIG.Default;
    const sRect = sourceEl.getBoundingClientRect();
    const tRect = targetEl.getBoundingClientRect();
    const startX = sRect.left + sRect.width / 2;
    const startY = sRect.top + sRect.height / 2;
    const endX = tRect.left + tRect.width / 2;
    const endY = tRect.top + tRect.height / 2;

    const tl = gsap.timeline();
    for (let i = 0; i < amount; i++) {
      const p = document.createElement('img');
      const startIdx = config.isAnimated ? (Math.floor(Math.random() * config.count!) + 1) : 1;
      p.src = config.isAnimated ? `${config.path}${startIdx}.png` : config.path;
      p.className = 'fixed z-[9999] pointer-events-none w-8 h-8 md:w-12 md:h-12';
      p.style.imageRendering = 'pixelated';
      document.body.appendChild(p);

      const sX = startX + (Math.random() - 0.5) * 80;
      const sY = startY + (Math.random() - 0.5) * 80;
      gsap.set(p, { x: sX, y: sY, opacity: 0, scale: 0.8, rotation: Math.random() * 360 });

      if (config.isAnimated && config.count) {
        let currentFrame = startIdx;
        gsap.to({}, {
          duration: 0.08, repeat: -1,
          onRepeat: () => {
            currentFrame = (currentFrame % config.count!) + 1;
            p.src = `${config.path}${currentFrame}.png`;
          }
        });
      }

      tl.to(p, {
        opacity: 1,
        x: endX + (Math.random() - 0.5) * 120,
        y: endY + (Math.random() - 0.5) * 120,
        duration: 0.4 + Math.random() * 0.4,
        rotation: "+=240",
        ease: "power2.out",
        delay: i * 0.03,
        onComplete: () => {
          gsap.killTweensOf(p);
          gsap.to(p, { opacity: 0, scale: 0, duration: 0.2, onComplete: () => p.remove() });
        }
      }, 0);
    }
    return tl;
  },

  burstParticles: (targetEl: HTMLElement, type: string, amount: number = 10) => {
    const config = PARTICLE_CONFIG[type] || PARTICLE_CONFIG.Default;
    const rect = targetEl.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const tl = gsap.timeline();
    for (let i = 0; i < amount; i++) {
      const p = document.createElement('img');
      const startIdx = config.isAnimated ? (Math.floor(Math.random() * config.count!) + 1) : 1;
      p.src = config.isAnimated ? `${config.path}${startIdx}.png` : config.path;
      p.className = 'fixed z-[9999] pointer-events-none w-10 h-10 md:w-14 md:h-14';
      p.style.imageRendering = 'pixelated';
      document.body.appendChild(p);

      gsap.set(p, { x: centerX - 20, y: centerY - 20, opacity: 0, scale: 0.5, rotation: Math.random() * 360 });

      if (config.isAnimated && config.count) {
        let currentFrame = startIdx;
        gsap.to({}, {
          duration: 0.08, repeat: -1,
          onRepeat: () => {
            currentFrame = (currentFrame % config.count!) + 1;
            p.src = `${config.path}${currentFrame}.png`;
          }
        });
      }

      const angle = (i / amount) * Math.PI * 2 + (Math.random() * 0.5);
      const radius = 60 + Math.random() * 80;
      tl.to(p, {
        opacity: 1,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        scale: 2,
        duration: 0.6 + Math.random() * 0.4,
        ease: "power2.out",
        onComplete: () => {
          gsap.killTweensOf(p);
          gsap.to(p, { opacity: 0, scale: 0, duration: 0.3, onComplete: () => p.remove() });
        }
      }, 0);
    }
    return tl;
  },

  shake: (target: HTMLElement, intensity: number = 12) => {
    return gsap.to(target, {
      x: `random(-${intensity}, ${intensity})`,
      duration: 0.04, repeat: 12, yoyo: true,
      onComplete: () => gsap.set(target, { x: 0 })
    });
  },

  flash: (target: HTMLElement, color: string = "white") => {
    return gsap.timeline()
      .to(target, { filter: `brightness(3) drop-shadow(0 0 25px ${color})`, duration: 0.1 })
      .to(target, { filter: "none", duration: 0.1 });
  },

  beam: (sourceEl: HTMLElement, targetEl: HTMLElement, color: string) => {
    const beam = document.createElement('div');
    beam.style.position = 'fixed'; beam.style.zIndex = '9999'; beam.style.pointerEvents = 'none';
    beam.style.height = '14px';
    beam.style.background = `linear-gradient(to right, transparent, ${color}, white, ${color}, transparent)`;
    beam.style.boxShadow = `0 0 20px ${color}`;
    beam.style.borderRadius = '10px'; beam.style.transformOrigin = 'left center';
    document.body.appendChild(beam);
    const sRect = sourceEl.getBoundingClientRect();
    const tRect = targetEl.getBoundingClientRect();
    const startX = sRect.left + sRect.width / 2;
    const startY = sRect.top + sRect.height / 2;
    const endX = tRect.left + tRect.width / 2;
    const endY = tRect.top + tRect.height / 2;
    const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
    const distance = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
    gsap.set(beam, { x: startX, y: startY, rotation: angle, width: 0 });
    return gsap.timeline({ onComplete: () => beam.remove() })
      .to(beam, { width: distance, duration: 0.25, ease: "expo.out" })
      .to(beam, { height: 45, opacity: 0.4, duration: 0.15 })
      .to(beam, { opacity: 0, duration: 0.2 });
  },

  faint: (target: HTMLElement) => {
    return gsap.to(target, {
      y: 200, opacity: 0, scale: 0.6, rotateZ: 20, duration: 0.8, ease: "power2.in"
    });
  }
};

export const MoveTemplates = {
  physical: (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean, type: string, strikeAsset?: string) => {
    return new Promise<void>((resolve) => {
      const tl = gsap.timeline({ onComplete: () => resolve() });
      tl.add(ActionAtoms.physicalStrike(attacker, isPlayer));
      tl.add(() => {
         const strike = document.createElement('img');
         strike.src = strikeAsset || "/images/particles/star_gba.png";
         strike.className = 'fixed z-[9999] pointer-events-none w-20 h-20';
         strike.style.imageRendering = 'pixelated';
         document.body.appendChild(strike);
         const dRect = defender.getBoundingClientRect();
         gsap.set(strike, { x: dRect.left + dRect.width/2 - 40, y: dRect.top + dRect.height/2 - 40, scale: 0 });
         gsap.timeline({ onComplete: () => strike.remove() })
            .to(strike, { scale: 2.2, duration: 0.15, ease: "back.out(1.7)" })
            .to(strike, { opacity: 0, scale: 2.5, duration: 0.2 });
      }, "-=0.1");

      tl.add(() => {
         if (type === 'Fire') ActionAtoms.burstParticles(defender, 'Fire', 10);
         else if (type === 'Electric') ActionAtoms.burstParticles(defender, 'Electric', 8);
      }, "+=0.1");

      tl.add(ActionAtoms.shake(defender, 22), "-=0.2");
    });
  },

  projectile: (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean, type: string) => {
    return new Promise<void>((resolve) => {
      const tl = gsap.timeline({ onComplete: () => resolve() });
      tl.to(attacker, { scale: 1.15, duration: 0.15, yoyo: true, repeat: 1 });
      tl.add(ActionAtoms.spawnGBAParticles(attacker, defender, type, 15));
      tl.add(ActionAtoms.flash(defender, TYPE_COLORS[type] || "white"), "-=0.3");
      tl.add(ActionAtoms.shake(defender, 20), "-=0.2");
    });
  },

  beam: (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean, type: string) => {
    return new Promise<void>((resolve) => {
      const color = TYPE_COLORS[type] || "#ffffff";
      const tl = gsap.timeline({ onComplete: () => resolve() });
      tl.to(attacker, { scale: 1.25, duration: 0.3 });
      tl.add(ActionAtoms.beam(attacker, defender, color));
      tl.add(ActionAtoms.flash(defender, color), "-=0.2");
      tl.add(ActionAtoms.shake(defender, 30), "-=0.2");
      tl.to(attacker, { scale: 1, duration: 0.2 });
    });
  },

  status: (target: HTMLElement, type: string) => {
    return new Promise<void>((resolve) => {
      const color = TYPE_COLORS[type] || "#3b82f6";
      const tl = gsap.timeline({ onComplete: () => resolve() });
      tl.to(target, { y: -25, duration: 0.3, yoyo: true, repeat: 1 });
      tl.add(ActionAtoms.burstParticles(target, type, 12), 0);
      tl.to(target, { filter: `brightness(2) drop-shadow(0 0 15px ${color})`, duration: 0.3, repeat: 1, yoyo: true }, 0);
    });
  },

  statusDamage: (target: HTMLElement, type: 'Burn' | 'Poison') => {
    return new Promise<void>((resolve) => {
      const color = type === 'Burn' ? "#EE8130" : "#A33EA1";
      const tl = gsap.timeline({ onComplete: () => resolve() });
      tl.add(ActionAtoms.flash(target, color));
      tl.add(ActionAtoms.shake(target, 10), 0);
      if (type === 'Burn') tl.add(ActionAtoms.burstParticles(target, 'Fire', 8), 0);
    });
  }
};

const MOVE_CONFIG: Record<string, any> = moveAnimationsData;

export const resolveMoveAnimation = (moveName: string, moveType: string, category: string) => {
  const name = moveName.toLowerCase().replace(/[^a-z0-9]/g, '');
  const config = MOVE_CONFIG[name];
  const type = config?.type || moveType || "Normal";
  const cat = config?.template || category?.toLowerCase() || 'physical';
  const strikeAsset = config?.strikeAsset || null;

  if (cat === 'multiHit') return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.physical(attacker, defender, isPlayer, type, strikeAsset);
  if (cat === 'beam') return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.beam(attacker, defender, isPlayer, type);
  if (cat === 'projectile' || (cat === 'special' && !config)) return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.projectile(attacker, defender, isPlayer, type);
  if (cat === 'status') return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.status(isPlayer ? attacker : defender, type);
  return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.physical(attacker, defender, isPlayer, type, strikeAsset);
};
