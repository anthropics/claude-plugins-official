// The three first scenes: dark, soft, slow, made of gradients.
// Rules the dark scenes keep:
// no glyphs or text-sized marks; large, soft, slow shapes made of gradients (no filters, so no GPU is needed);
// the middle of the window, where the conversation sits, stays calm; the interest lives at the edges and corners.
const STILL = '@media (prefers-reduced-motion: reduce) { * { animation: none !important } }'

function open(style: string, defs: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style} ${STILL}</style><defs>${defs}</defs>`
}

function soft(id: string, color: string, peak: number): string {
  return `<radialGradient id="${id}"><stop offset="0" stop-color="${color}" stop-opacity="${peak}"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></radialGradient>`
}

// A hint of calm down the middle. The app lays its own veil on the text column and owns legibility; this only keeps the centre from being the busiest part.
const CALM = `<radialGradient id="calm" cx="0.5" cy="0.55" r="0.6"><stop offset="0" stop-color="#000" stop-opacity="0.12"/><stop offset="0.6" stop-color="#000" stop-opacity="0.05"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>`
const calm = '<rect width="1600" height="1000" fill="url(#calm)"/>'

/* Deep Water: light falling in from the top corners, slow caustic bands, a few big soft bubbles
   up the far edges, and one turtle as a quiet silhouette in the bottom right corner. */
export function deepWaterSvg(): string {
  return `${open(
  `.shaft{transform-origin:50% 0;animation:sway 38s ease-in-out infinite alternate}
   .shaft.b{animation-duration:52s;animation-direction:alternate-reverse}
   .band{animation:drift 70s ease-in-out infinite alternate}
   .band.b{animation-duration:95s;animation-direction:alternate-reverse}
   .bubble{animation:rise 46s linear infinite}
   .honu{animation:glide 80s ease-in-out infinite alternate}
   @keyframes sway{from{transform:skewX(-5deg)}to{transform:skewX(6deg)}}
   @keyframes drift{from{transform:translateX(-90px)}to{transform:translateX(90px)}}
   @keyframes rise{from{transform:translateY(0);opacity:0}12%{opacity:1}85%{opacity:1}to{transform:translateY(-1150px);opacity:0}}
   @keyframes glide{from{transform:translate(0,0) rotate(-4deg)}to{transform:translate(-70px,-26px) rotate(3deg)}}`,
  `<linearGradient id="deep" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f6f86"/><stop offset="0.45" stop-color="#0a4660"/><stop offset="1" stop-color="#041c30"/></linearGradient>
   <linearGradient id="ray" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#bff3ff" stop-opacity="0"/><stop offset="0.5" stop-color="#bff3ff" stop-opacity="0.3"/><stop offset="1" stop-color="#bff3ff" stop-opacity="0"/></linearGradient>
   <linearGradient id="down" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="0.92" stop-color="#000"/></linearGradient>
   <mask id="fade" maskUnits="userSpaceOnUse" x="-400" y="-40" width="2400" height="900"><rect x="-400" y="-40" width="2400" height="900" fill="url(#down)"/></mask>
   ${soft('caustic', '#9fe9f5', 0.2)}
   ${soft('orb', '#c9f6ff', 0.22)}${soft('glint', '#e8fdff', 0.3)}${CALM}`,
)}
<rect width="1600" height="1000" fill="url(#deep)"/>
<g mask="url(#fade)">
<g transform="translate(-60 0) skewX(-14)"><rect class="shaft" x="0" y="-40" width="460" height="900" fill="url(#ray)"/></g>
<g transform="translate(1180 0) skewX(11)"><rect class="shaft b" x="0" y="-40" width="520" height="900" fill="url(#ray)"/></g>
<g transform="translate(250 0) skewX(-20)"><rect class="shaft b" x="0" y="-40" width="420" height="900" fill="url(#ray)" opacity="0.55"/></g>
</g>
<g class="band"><ellipse cx="380" cy="130" rx="620" ry="70" fill="url(#caustic)"/><ellipse cx="1280" cy="170" rx="540" ry="56" fill="url(#caustic)"/></g>
<g class="band b"><ellipse cx="300" cy="900" rx="700" ry="80" fill="url(#caustic)"/><ellipse cx="1350" cy="880" rx="560" ry="64" fill="url(#caustic)"/></g>
<g class="bubble" style="animation-delay:-4s"><circle cx="70" cy="1060" r="46" fill="url(#orb)"/></g>
<g class="bubble" style="animation-delay:-21s"><circle cx="1535" cy="1080" r="62" fill="url(#orb)"/><circle cx="1518" cy="1060" r="15" fill="url(#glint)"/></g>
<g class="bubble" style="animation-delay:-33s"><circle cx="1470" cy="1050" r="30" fill="url(#orb)"/></g>
<g class="bubble" style="animation-delay:-14s"><circle cx="150" cy="1070" r="26" fill="url(#orb)"/></g>
<g transform="translate(1300 800)"><g class="honu" opacity="0.5"><g fill="#0b3a4d">
  <ellipse cx="0" cy="0" rx="92" ry="62"/>
  <ellipse cx="108" cy="-10" rx="30" ry="20"/>
  <path d="M40 -52 q60 -64 104 -40 q-44 10 -78 62z"/><path d="M36 52 q58 60 96 34 q-40 -6 -70 -54z"/>
  <path d="M-58 -44 q-52 -30 -70 -6 q38 0 56 34z"/><path d="M-58 44 q-50 30 -66 8 q36 -2 54 -34z"/>
  <path d="M-92 0 l-30 6 l28 6z"/></g>
  <ellipse cx="0" cy="0" rx="70" ry="44" fill="#124d63"/></g></g>
${calm}</svg>`
}

/* Aurora: a night sky that is almost black in the middle, with two wide ribbons of light swaying across the top
   and a low ridge along the very bottom. */
export function auroraSvg(): string {
  return `${open(
  `.ribbon{transform-origin:50% 0;animation:wave 44s ease-in-out infinite alternate}
   .ribbon.b{animation-duration:63s;animation-direction:alternate-reverse}
   .ribbon.c{transform-origin:50% 50%;animation-duration:90s}
   .haze{animation:breathe 30s ease-in-out infinite alternate}
   @keyframes wave{from{transform:translateX(-70px) skewX(-7deg) scaleY(0.94)}to{transform:translateX(70px) skewX(7deg) scaleY(1.08)}}
   @keyframes breathe{from{opacity:0.55}to{opacity:1}}`,
  `<linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c1136"/><stop offset="0.55" stop-color="#090b22"/><stop offset="1" stop-color="#05060f"/></linearGradient>
   ${soft('green', '#5dffb5', 0.3)}${soft('violet', '#9f7bff', 0.26)}${soft('glow', '#3affc0', 0.2)}${soft('dusk', '#7a5cff', 0.18)}${CALM}`,
)}
<rect width="1600" height="1000" fill="url(#night)"/>
<ellipse class="haze" cx="260" cy="80" rx="520" ry="260" fill="url(#glow)"/>
<ellipse class="haze" cx="1400" cy="60" rx="480" ry="240" fill="url(#dusk)" style="animation-delay:-12s"/>
<g class="ribbon"><ellipse cx="-40" cy="230" rx="330" ry="150" fill="url(#green)"/><ellipse cx="260" cy="170" rx="360" ry="170" fill="url(#green)"/><ellipse cx="600" cy="230" rx="340" ry="140" fill="url(#green)"/><ellipse cx="930" cy="160" rx="360" ry="150" fill="url(#green)"/><ellipse cx="1270" cy="110" rx="340" ry="140" fill="url(#green)"/><ellipse cx="1600" cy="170" rx="330" ry="150" fill="url(#green)"/></g>
<g class="ribbon b"><ellipse cx="80" cy="110" rx="340" ry="130" fill="url(#violet)"/><ellipse cx="460" cy="80" rx="360" ry="140" fill="url(#violet)"/><ellipse cx="860" cy="290" rx="330" ry="120" fill="url(#violet)"/><ellipse cx="1220" cy="270" rx="350" ry="130" fill="url(#violet)"/><ellipse cx="1560" cy="80" rx="340" ry="140" fill="url(#violet)"/></g>
<g class="ribbon c"><ellipse cx="90" cy="430" rx="300" ry="260" fill="url(#green)"/><ellipse cx="150" cy="700" rx="260" ry="220" fill="url(#violet)"/><ellipse cx="1510" cy="460" rx="300" ry="270" fill="url(#violet)"/><ellipse cx="1470" cy="720" rx="260" ry="220" fill="url(#green)"/><ellipse cx="800" cy="330" rx="520" ry="150" fill="url(#green)" opacity="0.5"/></g>
<path d="M0 1000 L0 930 L180 880 L330 925 L520 868 L700 930 L900 892 L1080 938 L1260 876 L1430 926 L1600 884 L1600 1000Z" fill="#03040b"/>
${calm}</svg>`
}

/* Ember: near-black with a warm glow pooled in the two bottom corners, and a handful of large soft embers
   drifting up beside the conversation. Nothing bright crosses the middle or the sidebar's rows on the far left. */
export function emberSvg(): string {
  return `${open(
  `.embers{animation:pulse 9s ease-in-out infinite alternate}
   .embers.b{animation-duration:13s;animation-direction:alternate-reverse}
   .ember{animation:lift 34s linear infinite}
   @keyframes pulse{from{opacity:0.6;transform:scale(0.97)}to{opacity:1;transform:scale(1.04)}}
   @keyframes lift{from{transform:translate(0,0);opacity:0}10%{opacity:0.9}70%{opacity:0.5}to{transform:translate(60px,-1100px);opacity:0}}`,
  `<linearGradient id="dusk2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d0709"/><stop offset="0.6" stop-color="#1c0b0e"/><stop offset="1" stop-color="#3a1210"/></linearGradient>
   ${soft('fire', '#ff7a2a', 0.5)}${soft('coal', '#ff3d1a', 0.34)}${soft('mote', '#ffc27a', 0.75)}${soft('dim', '#ffc27a', 0.22)}${CALM}`,
)}
<rect width="1600" height="1000" fill="url(#dusk2)"/>
<ellipse class="embers b" cx="1380" cy="40" rx="620" ry="300" fill="url(#coal)" opacity="0.28"/>
<g style="transform-origin:120px 1000px" class="embers"><ellipse cx="120" cy="1010" rx="640" ry="520" fill="url(#fire)"/></g>
<g style="transform-origin:1500px 1000px" class="embers b"><ellipse cx="1500" cy="1020" rx="680" ry="560" fill="url(#coal)"/></g>
<ellipse cx="800" cy="1060" rx="900" ry="160" fill="url(#coal)" opacity="0.5"/>
<circle class="ember" cx="470" cy="1040" r="14" fill="url(#mote)" style="animation-delay:-3s"/>
<circle class="ember" cx="560" cy="1060" r="10" fill="url(#mote)" style="animation-delay:-17s"/>
<circle class="ember" cx="1380" cy="1050" r="18" fill="url(#mote)" style="animation-delay:-9s"/>
<circle class="ember" cx="1500" cy="1040" r="12" fill="url(#mote)" style="animation-delay:-25s"/>
<circle class="ember" cx="1250" cy="1070" r="9" fill="url(#mote)" style="animation-delay:-30s"/>
<circle class="ember" cx="120" cy="1080" r="18" fill="url(#dim)" style="animation-delay:-22s"/>
${calm}</svg>`
}

