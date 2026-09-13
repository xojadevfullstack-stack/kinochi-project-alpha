import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      keyframes: {
        'fade-in-up': {
          '0%': {
            opacity: '0',
            transform: 'translateY(20px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.8s ease-out forwards',
      },
      colors: {
        "on-secondary-container": "#b7b4b7",
        "on-secondary": "#303032",
        "on-secondary-fixed": "#1b1b1d",
        "on-tertiary-fixed": "#001b3c",
        "rating-gold": "#F59E0B",
        "tertiary-fixed-dim": "#a7c8ff",
        "surface-container-low": "#0D0E12",
        "on-primary": "#ffffff",
        "surface-bright": "#2C2F3A",
        "outline-variant": "#27272A",
        "error": "#ef4444",
        "surface-variant": "#1A1C24",
        "surface-container-high": "#1A1C23",
        "surface-tint": "#ffffff",
        "secondary-fixed": "#e5e1e4",
        "on-surface": "#ffffff",
        "tertiary-container": "#229ED9",
        "background": "#09090B",
        "surface-dim": "#09090B",
        "primary": "#E50914",
        "on-tertiary-fixed-variant": "#004689",
        "secondary-fixed-dim": "#c8c6c8",
        "outline": "#3F3F46",
        "primary-fixed-dim": "#E50914",
        "background-obsidian": "#09090B",
        "secondary": "#c8c6c8",
        "primary-container": "#E50914",
        "on-surface-variant": "#A1A1AA",
        "on-primary-fixed": "#ffffff",
        "on-secondary-fixed-variant": "#474649",
        "on-error-container": "#fca5a5",
        "tertiary": "#38BDF8",
        "inverse-primary": "#DC2626",
        "inverse-on-surface": "#09090B",
        "on-primary-container": "#ffffff",
        "surface-container-lowest": "#08080A",
        "surface-container": "#121317",
        "primary-fixed": "#E50914",
        "inverse-surface": "#ffffff",
        "on-tertiary-container": "#ffffff",
        "surface-container-highest": "#242731",
        "secondary-container": "#27272A",
        "on-error": "#ffffff",
        "error-container": "#7f1d1d",
        "text-secondary": "#A1A1AA",
        "text-primary": "#FFFFFF",
        "on-primary-fixed-variant": "#991b1b",
        "on-background": "#FFFFFF",
        "tertiary-fixed": "#e0f2fe",
        "on-tertiary": "#ffffff",
        "surface": "#0E0F13"
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      spacing: {
        "stack-lg": "32px",
        "gutter": "24px",
        "margin-mobile": "16px",
        "container-max": "1440px",
        "stack-sm": "8px",
        "stack-md": "16px",
        "margin-desktop": "48px"
      },
      fontFamily: {
        "headline-lg": ["var(--font-outfit)", "sans-serif"],
        "label-caps": ["var(--font-inter)", "sans-serif"],
        "body-lg": ["var(--font-inter)", "sans-serif"],
        "headline-md": ["var(--font-outfit)", "sans-serif"],
        "body-md": ["var(--font-inter)", "sans-serif"],
        "display-hero": ["var(--font-outfit)", "sans-serif"],
        "display-hero-mobile": ["var(--font-outfit)", "sans-serif"],
        // Adding default fallbacks in case standard classes are used
        "sans": ["var(--font-inter)", "sans-serif"],
        "display": ["var(--font-outfit)", "sans-serif"],
      },
      fontSize: {
        "headline-lg": ["32px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "700" }],
        "label-caps": ["12px", { lineHeight: "1", letterSpacing: "0.15em", fontWeight: "700" }],
        "body-lg": ["18px", { lineHeight: "1.6", fontWeight: "400" }],
        "headline-md": ["24px", { lineHeight: "1.3", fontWeight: "700" }],
        "body-md": ["16px", { lineHeight: "1.5", fontWeight: "400" }],
        "display-hero": ["72px", { lineHeight: "1.1", letterSpacing: "-0.04em", fontWeight: "900" }],
        "display-hero-mobile": ["40px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "900" }]
      }
    }
  },
  plugins: [],
};
export default config;
