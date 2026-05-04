# Design Guide

Fallback reference when the `frontend-design` and `humanizer` skills are not installed. Follow these rules for every landing page you build.

---

## The AI Slop Test

If you showed this interface to someone and said "AI made this," would they believe you immediately? If yes, redesign it.

A distinctive interface should make someone ask "how was this made?" — not "which AI made this?"

---

## Typography

**Load fonts via `next/font/google`.** Never use CDN links or system fonts.

### Banned Fonts
Inter, Roboto, Arial, Open Sans, Helvetica, system-ui defaults. These are the AI defaults.

### Recommended Pairings by Vibe

| Vibe | Headline | Body |
|------|----------|------|
| Elegant / Luxury | Playfair Display, Cormorant Garamond, EB Garamond | Lora, Source Serif 4, Crimson Text |
| Modern / Clean | Space Grotesk, Outfit, Plus Jakarta Sans | DM Sans, Manrope, Nunito Sans |
| Bold / Impactful | Syne, Clash Display (variable), Unbounded | Work Sans, Karla, Rubik |
| Playful / Warm | Fredoka, Baloo 2, Comfortaa | Quicksand, Poppins, Nunito |
| Professional | Instrument Serif, Literata, Fraunces | Inter (only as body with a distinctive headline), Atkinson Hyperlegible |
| Edgy / Experimental | Space Mono, JetBrains Mono, Major Mono Display | IBM Plex Sans, Geist Sans |

### Font Loading Pattern
```tsx
import { Space_Grotesk, DM_Sans } from "next/font/google";

const heading = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap",
});

const body = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

// In layout.tsx body tag:
<body className={`${heading.variable} ${body.variable} font-body`}>
```

### Typography System Architecture

**Vertical rhythm:** Line-height is the base unit for all spacing. If body line-height is 24px, all vertical spacing should be multiples of 24px (or 12px for half-rhythm).

**5-size modular scale using `clamp()`:**
```css
--text-xs:  clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
--text-sm:  clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
--text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
--text-lg:  clamp(1.25rem, 1rem + 1.25vw, 1.75rem);
--text-xl:  clamp(1.75rem, 1.2rem + 2.75vw, 3rem);
--text-2xl: clamp(2.25rem, 1.5rem + 3.75vw, 4.5rem);
```

**Font weight hierarchy:**
- 300 (Light): secondary text, captions
- 400 (Regular): body text
- 500 (Medium): subheadings, labels
- 600 (Semibold): section headings
- 700-800 (Bold/Extrabold): hero headlines only

**OpenType features:** Use `font-variant-numeric: tabular-nums` for aligned numbers (pricing, stats). Use `font-feature-settings: "liga" 1, "calt" 1` for contextual alternates.

**Measure:** Set `max-width: 65ch` on text blocks for optimal reading width.

### Rules
- Use `clamp()` for fluid sizing: `clamp(2rem, 5vw, 4rem)` for headlines
- Vary font weights to create hierarchy (300, 400, 600, 800)
- Never use monospace as a lazy shorthand for "technical"
- Don't put rounded icons above every heading — it looks templated

---

## Color

### Banned Palettes (The AI Aesthetic)
- Cyan/teal on dark backgrounds
- Purple-to-blue gradients
- Neon accents on dark mode
- Pure black (#000) or pure white (#fff)

### OKLCH Color System
Always use OKLCH for color definitions — it's perceptually uniform (HSL is not).

```css
:root {
  /* Primary palette */
  --color-primary: oklch(55% 0.15 250);       /* Brand blue */
  --color-primary-light: oklch(75% 0.10 250);
  --color-primary-dark: oklch(35% 0.15 250);

  /* Tinted neutrals (add brand hue at low chroma) */
  --color-surface: oklch(98% 0.01 250);        /* Near-white with blue tint */
  --color-surface-alt: oklch(95% 0.015 250);
  --color-text: oklch(15% 0.02 250);           /* Near-black with blue tint */
  --color-text-muted: oklch(45% 0.02 250);

  /* Accent */
  --color-accent: oklch(65% 0.20 30);          /* Warm coral */
}
```

**Tinted neutrals recipe:** Take your brand hue angle (e.g., 250 for blue). Use that hue for ALL neutrals with chroma between 0.005 and 0.02. This creates subconscious cohesion.

**Dark mode is NOT inverted light mode.** It requires:
- Different surface colors (not just swapped black/white)
- Reduced chroma on accent colors (bright saturated colors are harsh on dark)
- Lighter font weights (text appears heavier on dark backgrounds)
- Increased letter-spacing (+0.01em to 0.02em)

**60-30-10 rule:** 60% dominant (surfaces), 30% secondary (text, containers), 10% accent (CTAs, highlights). This is about visual weight, not pixel count.

### Rules
- Tint your neutrals toward your brand hue (even 2-3% creates cohesion)
- Use `oklch()` or `color-mix()` for perceptually uniform colors
- Dominant color + sharp accent outperforms evenly-distributed palettes
- No gray text on colored backgrounds — use a shade of the background color
- All text must pass WCAG AA contrast (4.5:1 for body, 3:1 for large text)

### Quick Palettes by Industry

| Industry | Primary | Accent | Neutrals |
|----------|---------|--------|----------|
| Food / Restaurant | Terracotta, warm brown | Sage green, gold | Cream, warm gray |
| Tech / SaaS | Deep navy, charcoal | Coral, amber | Cool off-white |
| Health / Wellness | Soft sage, eucalyptus | Warm blush, peach | Warm white |
| Finance / Law | Dark slate, forest green | Muted gold, copper | Cool cream |
| Creative / Design | Rich burgundy, deep teal | Hot orange, magenta | Near-black, off-white |
| Education | Ocean blue, indigo | Warm yellow, lime | Light gray, cream |

---

## Spacing & Layout System

### 4pt Base Unit
All spacing should be multiples of 4px: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128.

**Fluid spacing with `clamp()`:**
```css
--space-section: clamp(4rem, 8vw, 8rem);     /* Between major sections */
--space-component: clamp(1.5rem, 3vw, 3rem); /* Between components */
--space-element: clamp(0.5rem, 1vw, 1rem);   /* Between elements */
```

### Container Queries
Use `@container` for component-level responsiveness:
```css
.card-wrapper { container-type: inline-size; }

@container (min-width: 400px) {
  .card { flex-direction: row; }
}
```

### Responsive Grids Without Media Queries
```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: clamp(1rem, 2vw, 2rem);
}
```

### Touch Targets
All interactive elements must be at least 44x44px on touch devices. Use padding to expand small buttons/links to meet this minimum.

### Breakpoint Reference
| Name | Width | Use |
|------|-------|-----|
| Mobile | 375px | Base design |
| Tablet | 768px | First expansion |
| Desktop | 1024px | Full layout |
| Wide | 1440px | Max content width |

### Layout Rules
- Don't center everything. Left-aligned text with asymmetric layouts feels more designed.
- Create visual rhythm through varied spacing — tight groupings, generous separations.
- Break the grid intentionally for emphasis.
- Don't wrap everything in cards. Not everything needs a container.
- Never nest cards inside cards.
- Don't use identical card grids (icon + heading + text, repeated 3x).

### Standard Section Order
Unless the user specifies otherwise:
1. **Navigation** — simple, minimal
2. **Hero** — headline, subheadline, CTA button, optional visual
3. **Social proof strip** — logos, trust badges, or a key metric (optional)
4. **Features / Services** — 3-4 items, varied layout (not identical cards)
5. **Testimonials** — 1-3 quotes with names and roles
6. **CTA section** — repeat the main call to action
7. **Footer** — contact info, links, "Built with Claude Web Builder by Tododeia"

### Responsive
- Mobile-first: design for 375px, then expand
- Use CSS Grid and `@container` queries for component-level responsiveness
- Don't just shrink desktop layout — adapt it
- Navigation becomes a hamburger menu on mobile
- Use `@media (pointer: coarse)` to detect touch devices and increase target sizes
- Use `env(safe-area-inset-*)` for devices with notches

---

## Motion

### The 100/300/500 Timing Rule
- **100-150ms**: Micro-feedback (button press, toggle, hover)
- **200-300ms**: State transitions (tab switch, dropdown open, accordion)
- **300-500ms**: Layout changes (page transitions, modal entrance)
- **500-800ms**: Complex entrance animations (hero reveal, staggered list)

**Exit faster than enter:** Use ~75% of the entrance duration for exits.

### Easing
- Use exponential easing: `ease-out-quart` or `cubic-bezier(0.25, 1, 0.5, 1)`
- For spring-like motion in Framer Motion: `type: "spring", stiffness: 300, damping: 30`
- Never use bounce or elastic easing — it feels dated and tacky

### Rules
- Animate only `transform` and `opacity`, never layout properties (width, height, padding, margin)
- One well-orchestrated page load (staggered reveals) beats scattered micro-interactions
- Use Framer Motion for React animations
- Always respect `prefers-reduced-motion`

### Stagger Pattern (Framer Motion)
```tsx
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1, y: 0,
    transition: { duration: 0.5, ease: [0.25, 1, 0.5, 1] }
  }
};
```

### Reduced Motion Pattern
```tsx
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// In Framer Motion:
<motion.div
  initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: prefersReducedMotion ? 0 : 0.5 }}
/>
```

---

## Interaction States

Every interactive element must handle these 8 states:

| State | Visual Change | Tailwind Example |
|-------|--------------|-----------------|
| **Default** | Base appearance | `bg-primary text-primary-foreground` |
| **Hover** | Subtle brightness/scale shift | `hover:bg-primary/90` |
| **Focus** | Visible ring (keyboard only) | `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` |
| **Active** | Pressed/depressed feel | `active:scale-[0.98]` |
| **Disabled** | Faded, no pointer | `disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none` |
| **Loading** | Spinner or skeleton | Replace content with spinner, keep same dimensions |
| **Error** | Red border/text | `border-destructive text-destructive` |
| **Success** | Green confirmation | `border-green-500 text-green-700` |

**Focus management:**
- Use `:focus-visible` (not `:focus`) for keyboard-only focus rings
- Never use `outline: none` without providing a replacement focus indicator
- Tab order must match visual order

---

## UX Writing Principles

### Button Labels
Be specific: "Start free trial" not "Get started." "Send message" not "Submit." "Delete 5 items" not "Delete."

### Error Messages
Formula: (1) What happened? (2) Why? (3) How to fix?
- Bad: "Error occurred"
- Good: "We couldn't send your message. The email address looks incomplete. Check it and try again."

### CTA Hierarchy
- **Primary** (one per section): Filled button, bold color — the main action
- **Secondary**: Outlined button — alternative action
- **Tertiary**: Text link — least important action

### Empty States
Design empty states that teach the interface. Not just "Nothing here" but "Add your first project to get started."

---

## Copy & Content

### AI Writing Patterns to Avoid

These are the fingerprints of AI-generated text. Check every piece of copy against this list.

**Banned Words/Phrases:**
delve, tapestry, landscape, foster, showcase, vibrant, nestled, leverage, innovative, cutting-edge, game-changing, seamless, empower, harness, spearhead, holistic, synergy, robust, dynamic, elevate, transform, revolutionize, reimagine, curate, bespoke, craft (as a verb for text), navigate (metaphorical), at the heart of, in today's world, stands as a testament, serves as a reminder, it's worth noting, it's important to note, the broader implications

**Banned Patterns:**
- Starting with "In a world where..." or "In today's [adjective] landscape..."
- Rule of three lists: "whether you're a X, Y, or Z"
- Em dash overuse — especially multiple per paragraph — like this
- Every sentence being the same length
- Ending with "The future of [topic] is bright"
- Inflated significance: "This marks a pivotal moment in..."
- Vague attributions: "Experts say..." "Many believe..."

**Good Copy Habits:**
- Have opinions. "We build fast" beats "We deliver innovative solutions."
- Vary rhythm. Short punchy lines. Then longer ones.
- Be specific. Numbers, names, concrete details.
- Use "you" and "we" — it's a conversation, not a press release.
- First person is fine: "We started this because..." is more human than "Founded with the mission to..."

---

## Visual Details

### Do
- Intentional decorative elements that reinforce the brand
- Subtle texture or grain for warmth
- Custom illustrations or geometric patterns over stock photos
- Generous whitespace as a design element

### Don't
- Glassmorphism everywhere (blur effects, glass cards, glow borders)
- Rounded rectangles with generic drop shadows
- Sparklines as decoration (tiny charts that mean nothing)
- Gradient text on headings for "impact"
- Icons with rounded corners above every section heading
- Thick colored border on one side of a card

---

## Pre-Delivery Checklist

Before showing the landing page to the user, verify:

### Visual Consistency
- [ ] All spacing values are from the 4pt scale
- [ ] All font sizes are from the modular scale
- [ ] All colors are from the token palette (no random hex values)
- [ ] No emoji used as icons (use SVG: Lucide React)

### Interaction Quality
- [ ] Every clickable element has `cursor-pointer`
- [ ] Hover states have 150-300ms transitions
- [ ] All 8 states handled on buttons and form elements
- [ ] Focus rings visible for keyboard navigation

### Responsive
- [ ] Works at 375px (mobile)
- [ ] Works at 768px (tablet)
- [ ] Works at 1024px (desktop)
- [ ] Works at 1440px (wide desktop)
- [ ] Touch targets are at least 44x44px on mobile

### Performance
- [ ] No layout-triggering animations (only transform/opacity)
- [ ] Images sized correctly (not oversized)
- [ ] Fonts loaded via `next/font/google` with `display: "swap"`
- [ ] `prefers-reduced-motion` respected

### Accessibility
- [ ] Text contrast passes WCAG AA (4.5:1 body, 3:1 large)
- [ ] All images have `alt` text (decorative: `alt=""`)
- [ ] Heading hierarchy: one h1, then h2, h3 in order
- [ ] Semantic HTML: `<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`
- [ ] Keyboard navigation works (Tab through the page)
