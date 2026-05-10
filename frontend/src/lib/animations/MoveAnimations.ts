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
  Water_Bubble: { path: "/images/particles/water/bubble/", count: 1, isAnimated: false },
  Water_Droplet: { path: "/images/particles/water/droplet/", count: 8, isAnimated: true },
  Water_Jet: { path: "/images/particles/water/jet/", count: 4, isAnimated: true },
  Water_Wave: { path: "/images/particles/water/wave/", count: 1, isAnimated: false },
  Water: { path: "/images/particles/water/droplet/", count: 8, isAnimated: true },
  Electric: { path: "/images/particles/bolt_gba.png" },
  Grass: { path: "/images/particles/leaf_gba.png" },
  Fighting: { path: "/images/particles/slash_gba.png" },
  Normal: { path: "/images/particles/star_gba.png" },
  Default: { path: "/images/particles/star_gba.png" }
};

const preloadParticles = () => {
  if (typeof window === 'undefined') return;
  for(let i=1; i<=4; i++) new Image().src = `/images/particles/fire/${i}.png`;
  for(let i=1; i<=8; i++) new Image().src = `/images/particles/water/droplet/${i}.png`;
  for(let i=1; i<=4; i++) new Image().src = `/images/particles/water/jet/${i}.png`;
  new Image().src = `/images/particles/water/bubble/1.png`;
  new Image().src = `/images/particles/water/wave/1.png`;
  ['bolt_gba', 'leaf_gba', 'slash_gba', 'star_gba', 'fight/kick'].forEach(name => {
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

  spawnGBAParticles: (sourceEl: HTMLElement, targetEl: HTMLElement, type: string, amount: number = 12, isStream: boolean = false) => {
    const config = PARTICLE_CONFIG[type] || PARTICLE_CONFIG.Default;
    const sRect = sourceEl.getBoundingClientRect();
    const tRect = targetEl.getBoundingClientRect();
    const startX = sRect.left + sRect.width / 2;
    const startY = sRect.top + sRect.height / 2;
    const endX = tRect.left + tRect.width / 2;
    const endY = tRect.top + tRect.height / 2;

    const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;

    const tl = gsap.timeline();
    for (let i = 0; i < amount; i++) {
      const p = document.createElement('img');
      const startIdx = config.isAnimated ? (Math.floor(Math.random() * config.count!) + 1) : 1;
      p.src = config.count && config.path.endsWith('/') ? `${config.path}${startIdx}.png` : config.path;
      p.className = 'fixed z-[9999] pointer-events-none w-10 h-10 md:w-14 md:h-14';
      p.style.imageRendering = 'pixelated';
      document.body.appendChild(p);

      const sX = startX + (Math.random() - 0.5) * (isStream ? 20 : 80);
      const sY = startY + (Math.random() - 0.5) * (isStream ? 20 : 80);
      
      gsap.set(p, { 
        x: sX, y: sY, 
        opacity: 0, 
        scale: isStream ? 1.2 : 0.8, 
        rotation: isStream ? angle : Math.random() * 360 
      });

      if (config.isAnimated && config.count) {
        let currentFrame = startIdx;
        gsap.to({}, { duration: 0.08, repeat: -1, onRepeat: () => { currentFrame = (currentFrame % config.count!) + 1; p.src = `${config.path}${currentFrame}.png`; } });
      }

      tl.to(p, {
        opacity: 1,
        x: endX + (Math.random() - 0.5) * (isStream ? 30 : 120),
        y: endY + (Math.random() - 0.5) * (isStream ? 30 : 120),
        duration: isStream ? 0.35 : 0.4 + Math.random() * 0.4,
        ease: "none",
        delay: i * (isStream ? 0.015 : 0.03),
        onComplete: () => {
          gsap.killTweensOf(p);
          gsap.to(p, { opacity: 0, scale: 0, duration: 0.1, onComplete: () => p.remove() });
        }
      }, 0);
    }
    return tl;
  },

  burstParticles: (targetEl: HTMLElement, type: string, amount: number = 10, isGeyser: boolean = false) => {
    const config = PARTICLE_CONFIG[type] || PARTICLE_CONFIG.Default;
    const rect = targetEl.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = isGeyser ? rect.bottom : (rect.top + rect.height / 2);

    const tl = gsap.timeline();
    for (let i = 0; i < amount; i++) {
      const p = document.createElement('img');
      const startIdx = config.isAnimated ? (Math.floor(Math.random() * config.count!) + 1) : 1;
      p.src = config.count && config.path.endsWith('/') ? `${config.path}${startIdx}.png` : config.path;
      p.className = 'fixed z-[9999] pointer-events-none w-10 h-10 md:w-16 md:h-16';
      p.style.imageRendering = 'pixelated';
      document.body.appendChild(p);

      const offset = (Math.random() - 0.5) * (isGeyser ? 150 : 0);
      gsap.set(p, { x: centerX + offset, y: centerY, opacity: 0, scale: 0.5, rotation: isGeyser ? -90 : Math.random() * 360 });

      if (config.isAnimated && config.count) {
        let currentFrame = startIdx;
        gsap.to({}, { duration: 0.08, repeat: -1, onRepeat: () => { currentFrame = (currentFrame % config.count!) + 1; p.src = `${config.path}${currentFrame}.png`; } });
      }

      if (isGeyser) {
        tl.to(p, {
          opacity: 1,
          y: centerY - 300 - Math.random() * 200,
          scale: 2,
          duration: 0.6 + Math.random() * 0.4,
          ease: "power2.out",
          delay: i * 0.02,
          onComplete: () => {
            gsap.killTweensOf(p);
            gsap.to(p, { opacity: 0, scale: 0, duration: 0.3, onComplete: () => p.remove() });
          }
        }, 0);
      } else {
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
    }
    return tl;
  },

  shake: (target: HTMLElement, intensity: number = 12, duration: number = 0.5) => {
    return gsap.to(target, { x: `random(-${intensity}, ${intensity})`, duration: 0.04, repeat: Math.floor(duration / 0.04), yoyo: true, onComplete: () => gsap.set(target, { x: 0 }) });
  },

  flash: (target: HTMLElement, color: string = "white") => {
    return gsap.timeline().to(target, { filter: `brightness(3) drop-shadow(0 0 25px ${color})`, duration: 0.1 }).to(target, { filter: "none", duration: 0.1 });
  },
  faint: (target: HTMLElement) => {
    return gsap.to(target, { y: 200, opacity: 0, scale: 0.6, rotateZ: 20, duration: 0.8, ease: "power2.in" });
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
         gsap.timeline({ onComplete: () => strike.remove() }).to(strike, { scale: 2.2, duration: 0.15, ease: "back.out(1.7)" }).to(strike, { opacity: 0, scale: 2.5, duration: 0.2 });
      }, "-=0.1");
      tl.add(() => { ActionAtoms.burstParticles(defender, type, 10); }, "+=0.1");
      tl.add(ActionAtoms.shake(defender, 22), "-=0.2");
    });
  },

  stream: (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean, type: string) => {
    return new Promise<void>((resolve) => {
      const tl = gsap.timeline({ onComplete: () => resolve() });
      tl.to(attacker, { scale: 1.1, duration: 0.1, yoyo: true, repeat: 1 });
      tl.add(ActionAtoms.spawnGBAParticles(attacker, defender, type, 40, true));
      tl.add(ActionAtoms.flash(defender, TYPE_COLORS[type.split('_')[0]] || "white"), "-=0.4");
      tl.add(ActionAtoms.shake(defender, 18), "-=0.3");
    });
  },

  geyser: (target: HTMLElement, type: string) => {
    return new Promise<void>((resolve) => {
      const color = TYPE_COLORS[type.split('_')[0]] || "#3b82f6";
      const tl = gsap.timeline({ onComplete: () => resolve() });
      tl.add(ActionAtoms.flash(target, color));
      tl.add(ActionAtoms.shake(target, 25, 0.8));
      tl.add(ActionAtoms.burstParticles(target, type, 25, true), 0);
      tl.add(ActionAtoms.burstParticles(target, type, 20, true), 0.2);
    });
  },

  fullscreen: (container: HTMLElement, isPlayer: boolean, type: string, moveName: string) => {
    return new Promise<void>((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'absolute inset-0 z-[10] pointer-events-none';
      overlay.style.backgroundColor = 'rgba(0, 0, 0, 0)';
      container.appendChild(overlay);
      const tl = gsap.timeline({ onComplete: () => { overlay.remove(); resolve(); } });
      if (moveName === 'surf' || moveName === 'muddywater') {
        const waterWall = document.createElement('div');
        waterWall.className = 'absolute z-[20] pointer-events-none w-[200%] h-[200%]';
        const direction = isPlayer ? 'to top right' : 'to bottom left';
        waterWall.style.background = `linear-gradient(${direction}, transparent, rgba(0, 100, 255, 0.6), rgba(255, 255, 255, 0.4), rgba(0, 100, 255, 0.6), transparent)`;
        waterWall.style.boxShadow = '0 0 100px rgba(0, 100, 255, 0.5)';
        container.appendChild(waterWall);
        const startX = isPlayer ? '-200%' : '100%';
        const endX = isPlayer ? '100%' : '-200%';
        const startY = isPlayer ? '100%' : '-200%';
        const endY = isPlayer ? '-200%' : '100%';
        gsap.set(waterWall, { x: startX, y: startY, rotation: isPlayer ? -15 : 165 });
        tl.to(overlay, { backgroundColor: 'rgba(0, 100, 255, 0.25)', duration: 0.4 })
          .to(waterWall, { x: endX, y: endY, duration: 1.6, ease: "power1.inOut", onComplete: () => waterWall.remove() }, 0.2)
          .to(overlay, { backgroundColor: 'rgba(0, 100, 255, 0)', duration: 0.4 }, "-=0.4");
      } else if (moveName === 'earthquake') {
        tl.to(overlay, { backgroundColor: 'rgba(101, 67, 33, 0.3)', duration: 0.2 })
          .to(overlay, { backgroundColor: 'rgba(101, 67, 33, 0)', duration: 0.3 }, "+=0.8");
      }
    });
  }
};

const MOVE_CONFIG: Record<string, any> = moveAnimationsData;

export const resolveMoveAnimation = (moveName: string, moveType: string, category: string, arenaRef?: HTMLElement) => {
  const name = moveName.toLowerCase().replace(/[^a-z0-9]/g, '');
  const config = MOVE_CONFIG[name];
  let type = config?.type || moveType || "Normal";
  const cat = config?.template || category?.toLowerCase() || 'physical';
  const strikeAsset = config?.strikeAsset || null;

  if (type === 'Water') {
    if (name.includes('bubble')) type = 'Water_Bubble';
    else if (name.includes('surf') || name.includes('muddywater')) type = 'Water_Wave';
    else if (name.includes('gun') || name.includes('pump') || name.includes('jet') || name.includes('waterfall') || name.includes('pulse')) type = 'Water_Jet';
    else type = 'Water_Droplet';
  }

  // GEEYSER MOVES
  if (name === 'waterfall' || name === 'originpulse') {
    return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.geyser(defender, type);
  }

  // STREAM MOVES
  if (name === 'hydropump' || name === 'watergun' || name === 'bubblebeam') {
    return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.stream(attacker, defender, isPlayer, type);
  }

  if (name === 'surf' || name === 'muddywater' || name === 'earthquake') {
    return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => {
      const p1 = arenaRef ? MoveTemplates.fullscreen(arenaRef, isPlayer, type, name) : Promise.resolve();
      const p2 = ActionAtoms.shake(defender, name === 'earthquake' ? 40 : 25, 1.2);
      return Promise.all([p1, p2]);
    };
  }

  if (cat === 'multiHit') return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.physical(attacker, defender, isPlayer, type, strikeAsset);
  if (cat === 'beam') return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => {
    const baseType = type.split('_')[0];
    const color = TYPE_COLORS[baseType] || "#ffffff";
    const tl = gsap.timeline();
    tl.to(attacker, { scale: 1.25, duration: 0.3 });
    const beam = document.createElement('div');
    beam.style.position = 'fixed'; beam.style.zIndex = '9999'; beam.style.pointerEvents = 'none';
    beam.style.height = '14px';
    beam.style.background = `linear-gradient(to right, transparent, ${color}, white, ${color}, transparent)`;
    beam.style.boxShadow = `0 0 20px ${color}`;
    beam.style.borderRadius = '10px'; beam.style.transformOrigin = 'left center';
    document.body.appendChild(beam);
    const sRect = attacker.getBoundingClientRect();
    const tRect = defender.getBoundingClientRect();
    const startX = sRect.left + sRect.width / 2;
    const startY = sRect.top + sRect.height / 2;
    const endX = tRect.left + tRect.width / 2;
    const endY = tRect.top + tRect.height / 2;
    const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
    const distance = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
    gsap.set(beam, { x: startX, y: startY, rotation: angle, width: 0 });
    return tl.to(beam, { width: distance, duration: 0.25, ease: "expo.out" })
      .to(beam, { height: 45, opacity: 0.4, duration: 0.15 })
      .add(ActionAtoms.flash(defender, color), "-=0.2")
      .add(ActionAtoms.shake(defender, 30), "-=0.2")
      .to(beam, { opacity: 0, duration: 0.2, onComplete: () => beam.remove() })
      .to(attacker, { scale: 1, duration: 0.2 });
  };
  if (cat === 'projectile' || (cat === 'special' && !config)) return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => {
    const tl = gsap.timeline();
    tl.to(attacker, { scale: 1.15, duration: 0.15, yoyo: true, repeat: 1 });
    tl.add(ActionAtoms.spawnGBAParticles(attacker, defender, type, 15));
    tl.add(ActionAtoms.flash(defender, TYPE_COLORS[type.split('_')[0]] || "white"), "-=0.3");
    tl.add(ActionAtoms.shake(defender, 20), "-=0.2");
    return tl;
  };
  if (cat === 'status') return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => {
    const target = isPlayer ? attacker : defender;
    const baseType = type.split('_')[0];
    const color = TYPE_COLORS[baseType] || "#3b82f6";
    const tl = gsap.timeline();
    tl.to(target, { y: -25, duration: 0.3, yoyo: true, repeat: 1 });
    tl.add(ActionAtoms.burstParticles(target, type, 12), 0);
    tl.to(target, { filter: `brightness(2) drop-shadow(0 0 15px ${color})`, duration: 0.3, repeat: 1, yoyo: true }, 0);
    return tl;
  };
  return (attacker: HTMLElement, defender: HTMLElement, isPlayer: boolean) => MoveTemplates.physical(attacker, defender, isPlayer, type, strikeAsset);
};
