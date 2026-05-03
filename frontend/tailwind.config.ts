/** @type {import('tailwindcss').Config} */
const withOpacity = (cssVariable: string) => ({ opacityValue }: { opacityValue?: string }) => {
  if (opacityValue === undefined) {
    return `var(${cssVariable})`
  }

  const opacity = Number.parseFloat(opacityValue)

  if (Number.isNaN(opacity)) {
    return `var(${cssVariable})`
  }

  return `color-mix(in srgb, var(${cssVariable}) ${opacity * 100}%, transparent)`
}

export default {
  content: [
    "./app/**/*.{js,vue,ts}",
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
        sans: ['Geist Sans', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', 'monospace'],
        display: ['Geist Sans', 'Archivo', 'Inter Tight', 'var(--font-sans)']
      },
      colors: {
        // Backgrounds using CSS variables
        background: {
          base: withOpacity('--bg-base'),
          surface: withOpacity('--bg-surface'),
          raised: withOpacity('--bg-raised'),
          overlay: 'hsl(0, 0%, 18%, 0.8)',
          // Interactive states
          hover: withOpacity('--bg-hover'),
          'hover-subtle': withOpacity('--bg-hover-subtle'),
          active: withOpacity('--bg-active'),
          selected: withOpacity('--bg-selected')
        },
        // Text colors using CSS variables
        text: {
          primary: withOpacity('--text-primary'),
          secondary: withOpacity('--text-secondary'),
          muted: withOpacity('--text-muted'),
          disabled: withOpacity('--text-disabled')
        },
        // Card and borders
        card: {
          base: withOpacity('--bg-surface'),
          border: withOpacity('--border'),
        },
        // Border colors
        border: {
          DEFAULT: withOpacity('--border'),
          highlight: withOpacity('--highlight'),
          subtle: withOpacity('--border-subtle')
        },
        // Primary/Brand colors
        primary: {
          DEFAULT: withOpacity('--primary'),
          hover: withOpacity('--primary-hover'),
          bg: withOpacity('--primary-bg'),
          border: withOpacity('--primary-border')
        },
        // Semantic status colors using CSS variables
        status: {
          // Success states
          success: {
            DEFAULT: withOpacity('--status-success'),
            bg: withOpacity('--status-success-bg'),
            border: withOpacity('--status-success-border'),
            hover: 'hsl(158,100%,13%)'
          },
          // Error states
          error: {
            DEFAULT: withOpacity('--status-error'),
            bg: withOpacity('--status-error-bg'),
            border: withOpacity('--status-error-border'),
            hover: 'hsl(347, 77%, 18%)'
          },
          // Warning states
          warning: {
            DEFAULT: withOpacity('--status-warning'),
            bg: withOpacity('--status-warning-bg'),
            border: withOpacity('--status-warning-border'),
            hover: 'hsl(45, 85%, 18%)'
          },
          // Info states
          info: {
            DEFAULT: withOpacity('--status-info'),
            bg: withOpacity('--status-info-bg'),
            border: withOpacity('--status-info-border'),
            hover: 'hsl(199, 89%, 18%)'
          },
          // Retry states
          retry: {
            DEFAULT: withOpacity('--status-retry'),
            bg: withOpacity('--status-retry-bg'),
            border: withOpacity('--status-retry-border'),
            hover: 'hsl(24, 95%, 18%)'
          },
          // Neutral states
          neutral: {
            DEFAULT: withOpacity('--status-neutral'),
            bg: withOpacity('--status-neutral-bg'),
            border: withOpacity('--status-neutral-border'),
            hover: 'hsl(215, 20%, 18%)'
          },
          // Special states
          special: {
            DEFAULT: withOpacity('--status-special'),
            bg: withOpacity('--status-special-bg'),
            border: withOpacity('--status-special-border'),
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
        // Sheet slide animations
        'slide-in-from-right': 'slide-in-from-right 0.3s ease-out',
        'slide-out-to-right': 'slide-out-to-right 0.3s ease-out',
        'slide-in-from-left': 'slide-in-from-left 0.3s ease-out',
        'slide-out-to-left': 'slide-out-to-left 0.3s ease-out',
        'slide-in-from-top': 'slide-in-from-top 0.3s ease-out',
        'slide-out-to-top': 'slide-out-to-top 0.3s ease-out',
        'slide-in-from-bottom': 'slide-in-from-bottom 0.3s ease-out',
        'slide-out-to-bottom': 'slide-out-to-bottom 0.3s ease-out',
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
        },
        'slide-in-from-right': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-out-to-right': {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'slide-in-from-left': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-out-to-left': {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-100%)' },
        },
        'slide-in-from-top': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        'slide-out-to-top': {
          '0%': { transform: 'translateY(0)' },
          '100%': { transform: 'translateY(-100%)' },
        },
        'slide-in-from-bottom': {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        'slide-out-to-bottom': {
          '0%': { transform: 'translateY(0)' },
          '100%': { transform: 'translateY(100%)' },
        },
      }
    },
  },
  plugins: [],
}
