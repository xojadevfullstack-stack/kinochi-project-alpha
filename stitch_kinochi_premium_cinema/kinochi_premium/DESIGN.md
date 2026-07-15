---
name: Kinochi Premium
colors:
  surface: '#200e0c'
  surface-dim: '#200e0c'
  surface-bright: '#4a3330'
  surface-container-lowest: '#1a0908'
  surface-container-low: '#2a1614'
  surface-container: '#2e1a18'
  surface-container-high: '#3a2522'
  surface-container-highest: '#462f2c'
  on-surface: '#ffdad5'
  on-surface-variant: '#e9bcb6'
  inverse-surface: '#ffdad5'
  inverse-on-surface: '#412b28'
  outline: '#af8782'
  outline-variant: '#5e3f3b'
  surface-tint: '#ffb4aa'
  primary: '#ffb4aa'
  on-primary: '#690003'
  primary-container: '#e50914'
  on-primary-container: '#fff7f6'
  inverse-primary: '#c0000c'
  secondary: '#c8c6c8'
  on-secondary: '#303032'
  secondary-container: '#474649'
  on-secondary-container: '#b7b4b7'
  tertiary: '#a7c8ff'
  on-tertiary: '#003061'
  tertiary-container: '#0072d7'
  on-tertiary-container: '#f8f9ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad5'
  primary-fixed-dim: '#ffb4aa'
  on-primary-fixed: '#410001'
  on-primary-fixed-variant: '#930007'
  secondary-fixed: '#e5e1e4'
  secondary-fixed-dim: '#c8c6c8'
  on-secondary-fixed: '#1b1b1d'
  on-secondary-fixed-variant: '#474649'
  tertiary-fixed: '#d5e3ff'
  tertiary-fixed-dim: '#a7c8ff'
  on-tertiary-fixed: '#001b3c'
  on-tertiary-fixed-variant: '#004689'
  background: '#200e0c'
  on-background: '#ffdad5'
  surface-variant: '#462f2c'
  background-obsidian: '#09090B'
  text-primary: '#FFFFFF'
  text-secondary: '#A1A1AA'
  rating-gold: '#F5C518'
typography:
  display-hero:
    fontFamily: Outfit
    fontSize: 72px
    fontWeight: '900'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  display-hero-mobile:
    fontFamily: Outfit
    fontSize: 40px
    fontWeight: '900'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.15em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 1440px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

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