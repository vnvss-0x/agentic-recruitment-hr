import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0B0F1A',
          surface: '#131827',
        },
        cyan: {
          DEFAULT: '#00E5FF',
        },
        amber: {
          DEFAULT: '#FF8A65',
        },
        emerald: {
          DEFAULT: '#34D399',
        },
      },
      fontFamily: {
        sans: ['Instrument Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
} satisfies Config
