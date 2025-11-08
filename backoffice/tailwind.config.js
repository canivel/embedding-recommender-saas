/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        error: '#dc2626',
        warning: '#f59e0b',
        success: '#10b981',
        info: '#3b82f6',
      },
    },
  },
  plugins: [],
};
