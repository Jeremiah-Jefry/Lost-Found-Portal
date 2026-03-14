/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand:          '#3b82f6',
        'brand-dark':   '#2563eb',
        'brand-light':  '#dbeafe',
        'brand-xlight': '#eff6ff',
        surface:        '#f8fafc',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card:       '0 1px 3px 0 rgb(0 0 0/.06), 0 1px 2px -1px rgb(0 0 0/.04)',
        'card-hover': '0 10px 25px -5px rgb(0 0 0/.08), 0 4px 10px -6px rgb(0 0 0/.05)',
      },
    },
  },
  plugins: [],
}
