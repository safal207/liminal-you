import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0d0d11',
        accent: '#6fffe9',
        text: '#eaeaea'
      },
      keyframes: {
        breath: {
          '0%, 100%': {
            opacity: '0.55',
            transform: 'scale(1) translateY(0px)'
          },
          '50%': {
            opacity: '0.85',
            transform: 'scale(1.05) translateY(-6px)'
          }
        }
      },
      animation: {
        breath: 'breath 12s ease-in-out infinite'
      }
    }
  },
  plugins: []
};

export default config;
