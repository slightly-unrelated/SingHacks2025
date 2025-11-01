/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          navy: '#1B2B3D',
          blue: '#141E55',
          light: '#0066CC',
        },
        surface: {
          white: '#FFFFFF',
          grey: '#F5F7FA',
          iron: '#CCD0D1',
        },
        text: {
          primary: '#333333',
          secondary: '#666666',
        },
        risk: {
          low: '#28A745',
          medium: '#FFA500',
          high: '#A30000',
        }
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}
