/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Light mode colors
        surface: {
          light: '#FFFFFF',
          DEFAULT: '#F8FAFC',
          dark: '#0F172A',
        },
        primary: {
          50: '#F0F9F1',
          100: '#DDF1E2',
          200: '#BBE3C5',
          300: '#89CE9C',
          400: '#56B370',
          500: '#2E9A4F', // Brand Green
          600: '#237B3F',
          700: '#1B5D31',
          800: '#144224',
          900: '#0F2F1B',
        },
        brand: {
          green: '#2E9A4F',
          gold: '#EAB308', // Adjusting to a nice gold matching the logo
          "gold-light": '#FDE047',
        },
        accent: {
          cyan: '#06B6D4',
          green: '#10B981',
          gold: '#EAB308',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
