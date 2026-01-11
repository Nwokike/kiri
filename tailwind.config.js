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
        // Brand Colors from Logo
        'brand-green': '#2E9A4F',
        'brand-green-light': '#4CB86B',
        'brand-green-dark': '#1E7A3A',
        'brand-gold': '#D4A537',
        'brand-gold-light': '#E8C05A',
        'brand-gold-dark': '#B8922D',
        // Light mode surfaces
        'surface': '#FFFFFF',
        'surface-secondary': '#F9FAFB',
        'surface-tertiary': '#F3F4F6',
        // Dark mode surfaces  
        'dark': '#0F172A',
        'dark-secondary': '#1E293B',
        'dark-tertiary': '#334155',
        // Text colors (light mode)
        'content': '#111827',
        'content-secondary': '#4B5563',
        'content-muted': '#9CA3AF',
        // Text colors (dark mode)
        'content-light': '#F9FAFB',
        'content-light-secondary': '#D1D5DB',
        // Border colors
        'border': '#E5E7EB',
        'border-dark': '#374151',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Monaco', 'monospace'],
      },
      boxShadow: {
        'soft': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'medium': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'card': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },
    },
  },
  plugins: [],
}
