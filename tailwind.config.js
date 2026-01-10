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
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Base backgrounds (Zinc)
        background: {
          light: '#F8FAFC', // Slate-50
          DEFAULT: '#09090B', // Zinc-950
          dark: '#020202', // Zinc-950 (darker)
          surface: '#18181B', // Zinc-900
        },
        // Primary Brand (Emerald/Cyber Green)
        primary: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          300: '#6EE7B7',
          400: '#34D399',
          500: '#10B981', // Emerald-500
          600: '#059669',
          700: '#047857',
          800: '#065F46',
          900: '#064E3B',
          glow: '#10B981', // For box-shadows
        },
        // Secondary/Accent (Cyan/Science Blue)
        secondary: {
          400: '#22D3EE',
          500: '#06B6D4',
          glow: '#06B6D4',
        },
        // Text Colors
        paper: {
          DEFAULT: '#E4E4E7', // Zinc-200
          dim: '#A1A1AA', // Zinc-400
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-green': '0 0 10px rgba(16, 185, 129, 0.5)',
        'glow-cyan': '0 0 10px rgba(6, 182, 212, 0.5)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
