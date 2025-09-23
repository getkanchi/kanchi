/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', 'monospace'],
        display: ['Archivo', 'Inter Tight', 'var(--font-sans)']
      },
      colors: {
        background: {
          base: 'hsl(20, 14.3%, 4.1%)',
          primary: 'hsl(0, 0%, 15.75%)',
          overlay: 'hsla(250, 24%, 9%, 0.8)'
        },
        text: {
          primary: '#e9e9e2',
          secondary: '#a3a3a3',
          tertiary: 'hsl(0, 0%, 50%)',
          quaternary: 'hsl(0, 0%, 35%)'
        },
        card: {
          base: '#121212',
          border: '#29292980',
        },
        accent: {
          blue: 'hsl(220, 80%, 55%)',
          'blue-hover': 'hsl(220, 85%, 50%)'
        },
        // Semantic status colors - optimized for dark mode readability
        status: {
          // Success states - emerald green for positive completion
          success: {
            DEFAULT: 'hsl(158, 64%, 52%)', // Emerald-500 equivalent
            bg: 'hsla(158, 64%, 52%, 0.1)',
            border: 'hsla(158, 64%, 52%, 0.2)',
            hover: 'hsla(158, 64%, 52%, 0.15)'
          },
          // Error states - rose for errors that need attention
          error: {
            DEFAULT: 'hsl(347, 77%, 60%)', // Rose-500 but softer
            bg: 'hsla(347, 77%, 60%, 0.1)',
            border: 'hsla(347, 77%, 60%, 0.2)',
            hover: 'hsla(347, 77%, 60%, 0.15)'
          },
          // Warning states - amber for pending/waiting
          warning: {
            DEFAULT: 'hsl(38, 92%, 60%)', // Amber-500 equivalent
            bg: 'hsla(38, 92%, 60%, 0.1)',
            border: 'hsla(38, 92%, 60%, 0.2)',
            hover: 'hsla(38, 92%, 60%, 0.15)'
          },
          // Info states - sky blue for active/running
          info: {
            DEFAULT: 'hsl(199, 89%, 58%)', // Sky-500 equivalent
            bg: 'hsla(199, 89%, 58%, 0.1)',
            border: 'hsla(199, 89%, 58%, 0.2)',
            hover: 'hsla(199, 89%, 58%, 0.15)'
          },
          // Retry states - orange for caution/retry attempts
          retry: {
            DEFAULT: 'hsl(24, 95%, 58%)', // Orange-500 equivalent
            bg: 'hsla(24, 95%, 58%, 0.1)',
            border: 'hsla(24, 95%, 58%, 0.2)',
            hover: 'hsla(24, 95%, 58%, 0.15)'
          },
          // Neutral states - slate for cancelled/revoked/offline
          neutral: {
            DEFAULT: 'hsl(215, 20%, 65%)', // Slate-400 equivalent
            bg: 'hsla(215, 20%, 65%, 0.1)',
            border: 'hsla(215, 20%, 65%, 0.2)',
            hover: 'hsla(215, 20%, 65%, 0.15)'
          },
          // Special states - violet for received/acknowledged
          special: {
            DEFAULT: 'hsl(263, 70%, 65%)', // Violet-500 equivalent
            bg: 'hsla(263, 70%, 65%, 0.1)',
            border: 'hsla(263, 70%, 65%, 0.2)',
            hover: 'hsla(263, 70%, 65%, 0.15)'
          }
        },
        // Legacy colors for backward compatibility
        success: 'hsl(158, 64%, 52%)',
        warning: 'hsl(38, 92%, 60%)',
        error: 'hsl(347, 77%, 60%)',
        info: 'hsl(199, 89%, 58%)'
      },
      borderRadius: {
        'base': '0.25rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem'
      },
      boxShadow: {
        'glow-sm': '0 0 10px hsla(220, 80%, 55%, 0.1)',
        'glow-md': '0 0 20px hsla(220, 80%, 55%, 0.15)',
        'glow-lg': '0 0 30px hsla(220, 80%, 55%, 0.2)'
      },
      transitionDuration: {
        '75': '75ms',
        '100': '100ms',
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
        '500': '500ms',
        '700': '700ms',
        '1000': '1000ms'
      },
      transitionTimingFunction: {
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-relaxed': 'pulse-relaxed 3s ease-in-out infinite',
      },
      keyframes: {
        'pulse-relaxed': {
          '0%, 100%': { 
            opacity: '0.1',
            transform: 'scale(1)'
          },
          '50%': { 
            opacity: '0.8',
            transform: 'scale(1.6)'
          },
        }
      }
    },
  },
  plugins: [],
}

