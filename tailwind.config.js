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
        // Kiri Brand Colors (from logo)
        'kiri': {
          green: '#0D7C3D',
          'green-dark': '#0A5C2C',
          'green-light': '#E8F5ED',
          'green-hover': '#0B6A34',
          gold: '#C4992E',
          'gold-dark': '#A67D1F',
          'gold-light': '#FDF5E6',
          'gold-hover': '#B38A28',
        },

        // Structure Colors (Light Mode)
        'bg': {
          primary: '#FFFFFF',
          secondary: '#F8F9FA',
          tertiary: '#E9ECEF',
        },
        'border': {
          DEFAULT: '#DEE2E6',
          strong: '#ADB5BD',
        },
        'text': {
          primary: '#212529',
          secondary: '#495057',
          tertiary: '#6C757D',
          muted: '#ADB5BD',
        },

        // Dark Mode
        'dark': {
          bg: '#121212',
          surface: '#1E1E1E',
          'surface-elevated': '#2D2D2D',
          border: '#3D3D3D',
          text: '#E4E4E7',
          secondary: '#A1A1AA',
        },

        // Semantic Colors
        'success': '#0D7C3D',
        'warning': '#C4992E',
        'error': '#DC3545',
        'info': '#0D6EFD',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Monaco', 'monospace'],
      },
      borderRadius: {
        'none': '0',
        'sm': '4px',
        DEFAULT: '6px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'card': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'dropdown': '0 4px 16px rgba(0, 0, 0, 0.12)',
        'elevated': '0 8px 24px rgba(0, 0, 0, 0.15)',
      },
    },
  },
  plugins: [],
}
