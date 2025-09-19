# Design Tokens & System Documentation

> A comprehensive design system inspired by modern web applications including Linear, Railway, Marijana Pav, and EchoTab.

## Core Design Principles

### Philosophy
- **Minimalism First**: Focus on essential elements, remove visual clutter
- **Performance & Speed**: Prioritize fast interactions and smooth transitions
- **Accessibility**: Dark/light mode support, high contrast ratios
- **Craft & Precision**: Attention to detail in every interaction
- **Functional Beauty**: Aesthetics serve function, not the reverse

## Color System

### Base Colors

#### Dark Theme
```css
--color-background-primary: hsl(250, 24%, 9%);     /* #0a0a0f - Deep space black */
--color-background-secondary: hsl(250, 20%, 12%);  /* #13131a - Elevated surface */
--color-background-tertiary: hsl(250, 18%, 15%);   /* #1a1a23 - Card background */
--color-background-overlay: hsla(250, 24%, 9%, 0.8); /* Modal/overlay background */

--color-text-primary: hsl(0, 0%, 95%);             /* #f2f2f2 - Main text */
--color-text-secondary: hsl(0, 0%, 70%);           /* #b3b3b3 - Muted text */
--color-text-tertiary: hsl(0, 0%, 50%);            /* #808080 - Subtle text */
--color-text-quaternary: hsl(0, 0%, 35%);          /* #595959 - Very subtle */
```

#### Light Theme
```css
--color-background-primary: hsl(0, 0%, 100%);      /* #ffffff - Pure white */
--color-background-secondary: hsl(0, 0%, 98%);     /* #fafafa - Off white */
--color-background-tertiary: hsl(0, 0%, 96%);      /* #f5f5f5 - Light gray */
--color-background-overlay: hsla(0, 0%, 100%, 0.8);

--color-text-primary: hsl(0, 0%, 9%);              /* #171717 - Near black */
--color-text-secondary: hsl(0, 0%, 35%);           /* #595959 - Gray */
--color-text-tertiary: hsl(0, 0%, 55%);            /* #8c8c8c - Light gray */
--color-text-quaternary: hsl(0, 0%, 70%);          /* #b3b3b3 - Very light gray */
```

### Accent Colors
```css
/* Primary Actions */
--color-accent-blue: hsl(220, 80%, 55%);           /* #2563eb - Primary actions */
--color-accent-blue-hover: hsl(220, 85%, 50%);     /* #1e40af - Hover state */

/* Status Colors */
--color-success: hsl(152, 38%, 42%);               /* #42a05b - Success/positive */
--color-warning: hsl(44, 74%, 52%);                /* #d89c20 - Warning/caution */
--color-error: hsl(0, 72%, 51%);                   /* #dc2626 - Error/critical */
--color-info: hsl(180, 50%, 44%);                  /* #38a3a5 - Information */

/* Gradient Accents */
--gradient-primary: linear-gradient(135deg, hsl(220, 80%, 55%), hsl(270, 60%, 52%));
--gradient-secondary: linear-gradient(135deg, hsl(180, 50%, 44%), hsl(152, 38%, 42%));
--gradient-tertiary: linear-gradient(135deg, hsl(270, 60%, 52%), hsl(330, 60%, 52%));
```

## Typography

### Font Families
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace;
--font-display: 'Archivo', 'Inter Tight', var(--font-sans);
```

### Font Sizes
```css
/* Display Sizes */
--font-size-9xl: 8rem;      /* 128px - Hero headlines */
--font-size-8xl: 6rem;      /* 96px */
--font-size-7xl: 4.5rem;    /* 72px */
--font-size-6xl: 3.75rem;   /* 60px */
--font-size-5xl: 3rem;      /* 48px */
--font-size-4xl: 2.25rem;   /* 36px */
--font-size-3xl: 1.875rem;  /* 30px */
--font-size-2xl: 1.5rem;    /* 24px */
--font-size-xl: 1.25rem;    /* 20px */

/* Body Sizes */
--font-size-lg: 1.125rem;   /* 18px */
--font-size-base: 1rem;     /* 16px - Default */
--font-size-sm: 0.875rem;   /* 14px */
--font-size-xs: 0.75rem;    /* 12px */
--font-size-xxs: 0.625rem;  /* 10px */
```

### Font Weights
```css
--font-weight-thin: 100;
--font-weight-light: 300;
--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
--font-weight-black: 900;
```

### Line Heights
```css
--line-height-none: 1;
--line-height-tight: 1.25;
--line-height-snug: 1.375;
--line-height-normal: 1.5;
--line-height-relaxed: 1.625;
--line-height-loose: 2;
```

### Letter Spacing
```css
--letter-spacing-tighter: -0.05em;
--letter-spacing-tight: -0.025em;
--letter-spacing-normal: 0;
--letter-spacing-wide: 0.025em;
--letter-spacing-wider: 0.05em;
--letter-spacing-widest: 0.1em;
```

## Spacing System

### Base Unit: 4px
```css
--space-0: 0;
--space-px: 1px;
--space-0.5: 0.125rem;  /* 2px */
--space-1: 0.25rem;     /* 4px */
--space-1.5: 0.375rem;  /* 6px */
--space-2: 0.5rem;      /* 8px */
--space-2.5: 0.625rem;  /* 10px */
--space-3: 0.75rem;     /* 12px */
--space-3.5: 0.875rem;  /* 14px */
--space-4: 1rem;        /* 16px */
--space-5: 1.25rem;     /* 20px */
--space-6: 1.5rem;      /* 24px */
--space-7: 1.75rem;     /* 28px */
--space-8: 2rem;        /* 32px */
--space-9: 2.25rem;     /* 36px */
--space-10: 2.5rem;     /* 40px */
--space-11: 2.75rem;    /* 44px */
--space-12: 3rem;       /* 48px */
--space-14: 3.5rem;     /* 56px */
--space-16: 4rem;       /* 64px */
--space-20: 5rem;       /* 80px */
--space-24: 6rem;       /* 96px */
--space-28: 7rem;       /* 112px */
--space-32: 8rem;       /* 128px */
--space-36: 9rem;       /* 144px */
--space-40: 10rem;      /* 160px */
--space-44: 11rem;      /* 176px */
--space-48: 12rem;      /* 192px */
--space-52: 13rem;      /* 208px */
--space-56: 14rem;      /* 224px */
--space-60: 15rem;      /* 240px */
--space-64: 16rem;      /* 256px */
--space-72: 18rem;      /* 288px */
--space-80: 20rem;      /* 320px */
--space-96: 24rem;      /* 384px */
```

## Border Radius
```css
--radius-none: 0;
--radius-sm: 0.125rem;    /* 2px - Subtle rounding */
--radius-base: 0.25rem;   /* 4px - Default */
--radius-md: 0.375rem;    /* 6px - Medium components */
--radius-lg: 0.5rem;      /* 8px - Cards, modals */
--radius-xl: 0.75rem;     /* 12px - Large components */
--radius-2xl: 1rem;       /* 16px - Extra large */
--radius-3xl: 1.5rem;     /* 24px - Hero sections */
--radius-full: 9999px;    /* Pills, circles */
```

## Shadows

### Elevation System
```css
/* Subtle shadows for light theme */
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

/* Dark theme shadows (using color for glow effects) */
--shadow-glow-sm: 0 0 10px hsla(220, 80%, 55%, 0.1);
--shadow-glow-md: 0 0 20px hsla(220, 80%, 55%, 0.15);
--shadow-glow-lg: 0 0 30px hsla(220, 80%, 55%, 0.2);

/* Inset shadows for depth */
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
--shadow-inner-lg: inset 0 4px 6px -1px rgba(0, 0, 0, 0.1);
```

## Animation & Transitions

### Timing Functions
```css
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### Durations
```css
--duration-75: 75ms;
--duration-100: 100ms;
--duration-150: 150ms;
--duration-200: 200ms;
--duration-300: 300ms;
--duration-500: 500ms;
--duration-700: 700ms;
--duration-1000: 1000ms;
```

### Common Transitions
```css
/* Default transition for most interactions */
--transition-default: all var(--duration-150) var(--ease-in-out);

/* Specific transitions */
--transition-colors: color var(--duration-150) var(--ease-in-out), 
                     background-color var(--duration-150) var(--ease-in-out),
                     border-color var(--duration-150) var(--ease-in-out);
--transition-opacity: opacity var(--duration-150) var(--ease-in-out);
--transition-shadow: box-shadow var(--duration-150) var(--ease-in-out);
--transition-transform: transform var(--duration-150) var(--ease-in-out);
```

## Layout System

### Container Widths
```css
--container-xs: 20rem;     /* 320px */
--container-sm: 24rem;     /* 384px */
--container-md: 28rem;     /* 448px */
--container-lg: 32rem;     /* 512px */
--container-xl: 36rem;     /* 576px */
--container-2xl: 42rem;    /* 672px */
--container-3xl: 48rem;    /* 768px */
--container-4xl: 56rem;    /* 896px */
--container-5xl: 64rem;    /* 1024px */
--container-6xl: 72rem;    /* 1152px */
--container-7xl: 80rem;    /* 1280px */
--container-full: 100%;
```

### Breakpoints
```css
--breakpoint-xs: 475px;
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### Grid System
```css
/* 12-column grid */
--grid-cols-1: repeat(1, minmax(0, 1fr));
--grid-cols-2: repeat(2, minmax(0, 1fr));
--grid-cols-3: repeat(3, minmax(0, 1fr));
--grid-cols-4: repeat(4, minmax(0, 1fr));
--grid-cols-5: repeat(5, minmax(0, 1fr));
--grid-cols-6: repeat(6, minmax(0, 1fr));
--grid-cols-7: repeat(7, minmax(0, 1fr));
--grid-cols-8: repeat(8, minmax(0, 1fr));
--grid-cols-9: repeat(9, minmax(0, 1fr));
--grid-cols-10: repeat(10, minmax(0, 1fr));
--grid-cols-11: repeat(11, minmax(0, 1fr));
--grid-cols-12: repeat(12, minmax(0, 1fr));
```

## Component Patterns

### Buttons

#### Primary Button
```css
.btn-primary {
  background: var(--color-accent-blue);
  color: white;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-medium);
  transition: var(--transition-default);
}

.btn-primary:hover {
  background: var(--color-accent-blue-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
```

#### Secondary Button
```css
.btn-secondary {
  background: transparent;
  color: var(--color-text-primary);
  border: 1px solid var(--color-text-quaternary);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  transition: var(--transition-default);
}

.btn-secondary:hover {
  border-color: var(--color-text-secondary);
  background: var(--color-background-secondary);
}
```

#### Ghost Button
```css
.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  transition: var(--transition-default);
}

.btn-ghost:hover {
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
}
```

### Cards

```css
.card {
  background: var(--color-background-tertiary);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: var(--transition-default);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(255, 255, 255, 0.1);
}

.card-gradient {
  background: var(--gradient-primary);
  position: relative;
  overflow: hidden;
}

.card-gradient::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent, rgba(255, 255, 255, 0.1));
  opacity: 0;
  transition: opacity var(--duration-300);
}

.card-gradient:hover::before {
  opacity: 1;
}
```

### Input Fields

```css
.input {
  background: var(--color-background-secondary);
  border: 1px solid var(--color-text-quaternary);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-primary);
  transition: var(--transition-default);
}

.input:focus {
  outline: none;
  border-color: var(--color-accent-blue);
  box-shadow: 0 0 0 3px hsla(220, 80%, 55%, 0.1);
}

.input::placeholder {
  color: var(--color-text-tertiary);
}
```

### Modals/Overlays

```css
.modal-overlay {
  background: var(--color-background-overlay);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.modal-content {
  background: var(--color-background-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-2xl);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: var(--space-8);
  max-width: var(--container-2xl);
}
```

## Interactive States

### Hover States
- Scale: 1.02 - 1.05 for clickable elements
- Opacity: 0.8 for secondary actions
- Color shift: Lighter/darker by 10-15%
- Elevation: Increase shadow by one level

### Focus States
- Outline: 2px solid accent color with 3px offset
- Box shadow: 0 0 0 3px with 10% opacity accent color
- Never remove focus indicators

### Active States
- Scale: 0.98 for pressed effect
- Darker background by 20%
- Reduced shadow

### Disabled States
- Opacity: 0.5
- Cursor: not-allowed
- Remove hover effects

## Accessibility Guidelines

### Color Contrast
- Normal text: Minimum 4.5:1 ratio
- Large text: Minimum 3:1 ratio
- Interactive elements: Minimum 3:1 ratio against background

### Focus Management
- All interactive elements must be keyboard accessible
- Focus order must be logical
- Focus indicators must be clearly visible

### Motion
- Respect prefers-reduced-motion
- Provide alternatives for motion-based interactions
- Keep animations under 300ms for responsiveness

## Performance Optimization

### CSS Variables Strategy
- Use CSS custom properties for all tokens
- Enable runtime theme switching
- Reduce CSS bundle size

### Animation Performance
- Use transform and opacity for animations
- Avoid animating layout properties
- Use will-change sparingly

### Loading Strategy
- Critical CSS inline
- Non-critical CSS lazy load
- Use CSS containment for complex components

## Implementation Example

```css
:root {
  /* Load all design tokens */
  @import 'design-tokens.css';
}

/* Dark theme */
[data-theme="dark"] {
  --color-background-primary: hsl(250, 24%, 9%);
  --color-text-primary: hsl(0, 0%, 95%);
  /* ... other dark theme tokens */
}

/* Light theme */
[data-theme="light"] {
  --color-background-primary: hsl(0, 0%, 100%);
  --color-text-primary: hsl(0, 0%, 9%);
  /* ... other light theme tokens */
}

/* Responsive typography */
@media (max-width: 768px) {
  :root {
    --font-size-base: 0.875rem;
    --font-size-lg: 1rem;
    /* Scale down other sizes proportionally */
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Design Token Usage Guidelines

1. **Consistency**: Always use tokens, never hardcode values
2. **Semantic Naming**: Use purpose-based names (e.g., `--color-error` not `--color-red`)
3. **Scalability**: Design tokens should work across all screen sizes
4. **Documentation**: Document any custom tokens or overrides
5. **Testing**: Test all color combinations for accessibility

## Inspiration Sources

- **Linear**: Minimalist design, focus on productivity, dark theme excellence
- **Railway**: Gradient usage, technical aesthetic, infrastructure metaphors
- **Marijana Pav**: Modern typography, creative layouts, smooth interactions
- **EchoTab**: Clean minimalism, efficient space usage, developer-friendly

---

*This design system is a living document. Update regularly based on user feedback and evolving design trends.*