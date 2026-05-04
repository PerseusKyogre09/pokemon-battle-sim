'use client';

import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { CloudRain, Sun, Wind, Snowflake } from 'lucide-react';

interface WeatherOverlayProps {
  weather: string;
}

export default function WeatherOverlay({ weather }: WeatherOverlayProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { contextSafe } = useGSAP({ scope: containerRef });

  useEffect(() => {
    if (!containerRef.current) return;
    
    // Clear previous animations
    const container = containerRef.current;
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    if (weather === 'none') return;

    if (weather === 'raindance') {
      createRain();
    } else if (weather === 'sunnyday') {
      createSun();
    } else if (weather === 'sandstorm') {
      createSandstorm();
    } else if (weather === 'hail') {
      createSnow();
    }
  }, [weather]);

  const createRain = contextSafe(() => {
    const container = containerRef.current;
    if (!container) return;

    for (let i = 0; i < 150; i++) {
      const drop = document.createElement('div');
      // Thicker, longer, and slanted drops
      drop.className = 'absolute bg-blue-400/50 w-[2px] h-[25px] rounded-full pointer-events-none z-10';
      container.appendChild(drop);

      gsap.set(drop, {
        x: Math.random() * (container.offsetWidth + 300) - 100, // Extra width for slant
        y: -40,
        opacity: Math.random() * 0.5 + 0.3,
        rotation: -25 // Slanted left (/)
      });

      gsap.to(drop, {
        y: container.offsetHeight + 40,
        x: '-=150', // Move left as it falls
        duration: Math.random() * 0.3 + 0.3, // Slightly faster rain
        repeat: -1,
        ease: 'none',
        delay: Math.random() * 2
      });
    }
  });

  const createSun = contextSafe(() => {
    const container = containerRef.current;
    if (!container) return;

    const sun = document.createElement('div');
    sun.className = 'absolute top-10 right-10 w-32 h-32 bg-yellow-400/20 blur-3xl rounded-full pointer-events-none';
    container.appendChild(sun);

    gsap.to(sun, {
      scale: 1.5,
      opacity: 0.4,
      duration: 2,
      repeat: -1,
      yoyo: true,
      ease: 'sine.inOut'
    });

    const overlay = document.createElement('div');
    overlay.className = 'absolute inset-0 bg-orange-500/10 pointer-events-none mix-blend-overlay';
    container.appendChild(overlay);
  });

  const createSandstorm = contextSafe(() => {
    const container = containerRef.current;
    if (!container) return;

    for (let i = 0; i < 100; i++) {
      const sand = document.createElement('div');
      sand.className = 'absolute bg-amber-600/60 w-[6px] h-[3px] rounded-full pointer-events-none z-10';
      container.appendChild(sand);

      gsap.set(sand, {
        x: -20,
        y: Math.random() * container.offsetHeight,
        opacity: Math.random() * 0.6 + 0.2,
        scale: Math.random() * 1.5 + 0.5
      });

      gsap.to(sand, {
        x: container.offsetWidth + 20,
        y: '+=100',
        duration: Math.random() * 0.8 + 0.4,
        repeat: -1,
        ease: 'none',
        delay: Math.random() * 2
      });
    }
    
    const dust = document.createElement('div');
    dust.className = 'absolute inset-0 bg-amber-900/10 pointer-events-none mix-blend-multiply z-0';
    container.appendChild(dust);
  });

  const createSnow = contextSafe(() => {
    const container = containerRef.current;
    if (!container) return;

    for (let i = 0; i < 60; i++) {
      const ice = document.createElement('div');
      ice.className = 'absolute bg-white/70 w-[4px] h-[4px] rounded-full pointer-events-none shadow-[0_0_8px_rgba(255,255,255,0.8)] z-10';
      container.appendChild(ice);

      gsap.set(ice, {
        x: Math.random() * container.offsetWidth,
        y: -20,
        opacity: Math.random() * 0.5 + 0.3
      });

      gsap.to(ice, {
        y: container.offsetHeight + 20,
        x: `+=${Math.random() * 100 - 50}`,
        rotation: Math.random() * 360,
        duration: Math.random() * 3 + 4, // 4 to 7 seconds
        repeat: -1,
        ease: 'none',
        delay: Math.random() * 5
      });
    }
  });

  if (weather === 'none') return null;

  return (
    <div ref={containerRef} className="absolute inset-0 pointer-events-none z-30 overflow-hidden rounded-xl">
      {/* Weather Indicator Icon - Adjusted top to be visible within arena */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-1.5 glass-panel border border-white/10 rounded-full animate-fade-in z-50">
        {weather === 'raindance' && (
          <>
            <CloudRain className="w-3 h-3 md:w-4 md:h-4 text-blue-400" />
            <span className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-blue-400 whitespace-nowrap">Rainy Condition</span>
          </>
        )}
        {weather === 'sunnyday' && (
          <>
            <Sun className="w-3 h-3 md:w-4 md:h-4 text-yellow-400" />
            <span className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-yellow-400 whitespace-nowrap">Harsh Sunlight</span>
          </>
        )}
        {weather === 'sandstorm' && (
          <>
            <Wind className="w-3 h-3 md:w-4 md:h-4 text-amber-500" />
            <span className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-amber-500 whitespace-nowrap">Sandstorm Active</span>
          </>
        )}
        {weather === 'hail' && (
          <>
            <Snowflake className="w-3 h-3 md:w-4 md:h-4 text-blue-200" />
            <span className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-blue-200 whitespace-nowrap">Snow Falling</span>
          </>
        )}
      </div>
    </div>
  );
}
