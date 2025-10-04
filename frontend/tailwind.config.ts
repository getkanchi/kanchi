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
        // Backgrounds using CSS variables
        background: {
          base: 'var(--bg-base)',
          surface: 'var(--bg-surface)',
          raised: 'var(--bg-raised)',
          overlay: 'hsl(0, 0%, 18%, 0.8)'
        },
        // Text colors using CSS variables
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
          disabled: 'var(--text-disabled)'
        },
        // Card and borders
        card: {
          base: 'var(--bg-surface)',
          border: 'var(--border)',
        },
        // Border colors
        border: {
          DEFAULT: 'var(--border)',
          highlight: 'var(--highlight)'
        },
        // Primary/Brand colors
        primary: {
          DEFAULT: 'var(--primary)',
          hover: 'var(--primary-hover)'
        },
        // Semantic status colors using CSS variables
        status: {
          // Success states
          success: {
            DEFAULT: 'var(--status-success)',
            bg: 'var(--status-success-bg)',
            border: 'var(--status-success-border)',
            hover: 'hsl(158, 100%, 18%)'
          },
          // Error states
          error: {
            DEFAULT: 'var(--status-error)',
            bg: 'var(--status-error-bg)',
            border: 'var(--status-error-border)',
            hover: 'hsl(347, 77%, 18%)'
          },
          // Warning states
          warning: {
            DEFAULT: 'var(--status-warning)',
            bg: 'var(--status-warning-bg)',
            border: 'var(--status-warning-border)',
            hover: 'hsl(45, 85%, 18%)'
          },
          // Info states
          info: {
            DEFAULT: 'var(--status-info)',
            bg: 'var(--status-info-bg)',
            border: 'var(--status-info-border)',
            hover: 'hsl(199, 89%, 18%)'
          },
          // Retry states
          retry: {
            DEFAULT: 'var(--status-retry)',
            bg: 'var(--status-retry-bg)',
            border: 'var(--status-retry-border)',
            hover: 'hsl(24, 95%, 18%)'
          },
          // Neutral states
          neutral: {
            DEFAULT: 'var(--status-neutral)',
            bg: 'var(--status-neutral-bg)',
            border: 'var(--status-neutral-border)',
            hover: 'hsl(215, 20%, 18%)'
          },
          // Special states
          special: {
            DEFAULT: 'var(--status-special)',
            bg: 'var(--status-special-bg)',
            border: 'var(--status-special-border)',
            hover: 'hsl(263, 70%, 18%)'
          }
        }
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

