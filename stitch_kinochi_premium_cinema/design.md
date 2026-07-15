# Kinochi Premium Design System

## Overview
Kinochi is a premium, modern, and highly interactive movie and series streaming platform (both user-facing website and an admin dashboard). The goal is to completely redesign the entire system from scratch with a brand new, highly polished, and cinematic aesthetic.

## Aesthetic & Vibe
- **Style:** Modern, Sleek, Cinematic, Premium, Netflix/Max-inspired.
- **Vibe:** Immersive, dark, dynamic, high-end.
- **Key Concepts:** Glassmorphism, Micro-animations, Neon-glow accents, High-contrast dark mode.

## Color Palette
- **Background (Primary):** #09090B (Deep Obsidian Black) - solid background for depth.
- **Background (Secondary/Surface):** #121214 (Dark Slate) - used for cards, sidebars, and modals.
- **Accent/Brand (Primary):** #E50914 (Cinematic Red) - used for primary CTAs, hover states, and active links. Include glowing effects (e.g., `drop-shadow(0 0 10px rgba(229,9,20,0.5))`).
- **Text (Primary):** #FFFFFF (Pure White) - for headings and primary content.
- **Text (Secondary):** #A1A1AA (Cool Gray) - for descriptions, metadata, and subtitles.
- **Rating Star:** #F5C518 (IMDb Yellow) - exclusively for star icons and rating badges.

## Typography
- **Heading Font:** 'Outfit', 'Inter', or 'Display' sans-serif (Bold, Black). Headings should be tight, tracking-tighter, and highly legible.
- **Body Font:** 'Inter' or 'Roboto' (Regular, Medium). Clean and highly readable.
- **Hierarchy:** 
  - H1: Giant, impactful, often with a slight text-shadow or drop-shadow for cinematic effect.
  - H2/H3: Clean, bold, easily scannable.
  - Badges/Metadata: Tiny, uppercase, wide letter-spacing (`tracking-widest`), font-bold.

## UI Elements & Components

### 1. Cards (Movies & Series)
- **Aspect Ratio:** 2:3 (Standard cinematic poster size).
- **Style:** Clean edges, subtle rounded corners (`rounded-xl`), no borders by default.
- **Hover Effect (Micro-animation):** Scale up slightly (`hover:scale-105`), increase z-index, add a red or white glow (`hover:ring-2 hover:ring-primary/50` or shadow).
- **Content Placement:** Title, Year, and Rating must be placed **INSIDE** the card at the bottom, overlaid on a dark, smooth gradient (`bg-gradient-to-t from-black via-black/50 to-transparent`).
- **Empty States:** If no poster exists, use a dark surface with a faint icon and "Poster yo'q" text.

### 2. Glassmorphism & Overlays
- Use backdrop-blur (`backdrop-blur-md`, `backdrop-blur-lg`) extensively for fixed headers, floating navigation bars, modal backgrounds, and interactive buttons over images.
- Backgrounds behind the glass should have a slight white/gray tint (`bg-white/5` or `bg-white/10`) to create a frosted glass effect.

### 3. Buttons & Inputs
- **Primary Button:** Solid Red (`bg-primary`), rounded-full, with a subtle glow shadow. On hover, transform translate-y slightly and intensify the glow.
- **Secondary/Icon Button:** Circular, frosted glass (`bg-white/10 backdrop-blur`), subtle border (`border border-white/10`), changes to `bg-white/20` on hover.
- **Inputs/Search:** Pill-shaped (`rounded-full`), dark translucent background (`bg-surface/80`), icon on the left. Focus state should add a crisp white or red ring.

### 4. Hero Section (Detail Pages & Home)
- Massive, edge-to-edge background images of the movie/series.
- Deep cinematic gradient fading into the solid background color at the bottom and sides so text is 100% readable.
- Metadata (IMDb rating, Year, Genres) displayed as crisp, small badges.
- Large trailer iframe embedded directly into the page (aspect-video, rounded-2xl, with a play button overlay mock if video is not playing).

## Animations & Transitions
- All interactive elements must have a transition (`transition-all duration-300`).
- Use fade-ins for page loads and staggered reveals for grids of movie cards.
- Smooth hover states—nothing should feel abrupt.

## Admin Panel Specifics
- **Sidebar:** Fixed, glassmorphic or solid dark slate, highlighting the active tab with the primary red color and a subtle left border/glow.
- **Data Tables:** Clean rows, minimal borders (only bottom borders between rows `border-white/5`), hover effects on rows (`hover:bg-white/5`).
- **Forms:** Large, padded input fields, clearly separated labels, focus rings matching the brand color.

## Code Constraints
- Use Tailwind CSS for all styling.
- Use native Next.js `<Image />` for optimized images.
- Ensure 100% responsiveness (Mobile, Tablet, Desktop). Mobile should use horizontal scrolling for movie rows (hide-scrollbar) and grid layouts for "All Movies" pages.
