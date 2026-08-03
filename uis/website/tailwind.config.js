/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: '#0F1B2D',
        ocean: '#005B88',
        seafoam: '#52B7A8',
        amber: '#F59E0B',
        mist: '#F4F7FA',
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        body: ['IBM Plex Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
