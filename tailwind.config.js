/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
    './core/**/*.py',
    './publications/**/*.py',
    './projects/**/*.py',
    './users/**/*.py',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // Brand Colors
        'brand': {
          DEFAULT: '#18181B', // Zinc 900
          hover: '#27272A',   // Zinc 800
          foreground: "#FAFAFA",
          green: "#10B981",
          "green-dark": "#059669",
          gold: "#F59E0B",
        },
        'brand-green': {
          DEFAULT: '#10B981', // Emerald 500
          dark: '#059669',    // Emerald 600
        },
        'brand-gold': {
          DEFAULT: '#F59E0B', // Amber 500
          dark: '#D97706',    // Amber 600
        },
        'accent': {
          DEFAULT: '#3B82F6', // Blue 500 (Subtle accents)
          hover: '#2563EB',   // Blue 600
        },
        // Semantic Colors
        'success': '#10B981', // Emerald 500
        'warning': '#F59E0B', // Amber 500
        'error': '#EF4444',   // Red 500

        // Structure Colors (Light Mode)
        'bg': {
          primary: '#FFFFFF',
          secondary: '#FAFAFA', // Zinc 50
          tertiary: '#F4F4F5',  // Zinc 100
        },
        'border': {
          DEFAULT: '#E4E4E7',   // Zinc 200
          strong: '#D4D4D8',    // Zinc 300
        },
        'text': {
          primary: '#18181B',   // Zinc 900
          secondary: '#52525B', // Zinc 600
          tertiary: '#71717A',  // Zinc 500
        },

        // Dark Mode (Cyberpunk Research)
        'dark': {
          bg: '#09090B',        // Zinc 950
          surface: '#18181B',   // Zinc 900
          border: '#27272A',    // Zinc 800
          text: '#FAFAFA',      // Zinc 50
          secondary: '#A1A1AA', // Zinc 400
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Monaco', 'monospace'],
        display: ['Outfit', 'Inter', 'sans-serif'],
      },
      borderRadius: {
        'none': '0',
        'sm': '0.125rem',
        DEFAULT: '0.25rem',
        'md': '0.375rem',
        'lg': '0.5rem',
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
      }
    },
  },
  plugins: [],
}
