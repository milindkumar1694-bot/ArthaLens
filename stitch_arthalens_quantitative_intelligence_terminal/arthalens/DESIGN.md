---
name: ARTHALENS
colors:
  surface: '#031427'
  surface-dim: '#031427'
  surface-bright: '#2a3a4f'
  surface-container-lowest: '#000f21'
  surface-container-low: '#0b1c30'
  surface-container: '#102034'
  surface-container-high: '#1b2b3f'
  surface-container-highest: '#26364a'
  on-surface: '#d3e4fe'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#d3e4fe'
  inverse-on-surface: '#213145'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#7dffa2'
  on-secondary: '#003918'
  secondary-container: '#05e777'
  on-secondary-container: '#00622e'
  tertiary: '#ffe7e7'
  on-tertiary: '#680016'
  tertiary-container: '#ffc1c1'
  on-tertiary-container: '#b4002e'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#62ff96'
  secondary-fixed-dim: '#00e475'
  on-secondary-fixed: '#00210b'
  on-secondary-fixed-variant: '#005226'
  tertiary-fixed: '#ffdad9'
  tertiary-fixed-dim: '#ffb3b4'
  on-tertiary-fixed: '#40000a'
  on-tertiary-fixed-variant: '#920024'
  background: '#031427'
  on-background: '#d3e4fe'
  surface-variant: '#26364a'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.01em
  mono-xl:
    fontFamily: JetBrains Mono
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  mono-lg:
    fontFamily: JetBrains Mono
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 22px
    letterSpacing: -0.01em
  mono-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0em
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.02em
  mono-xs:
    fontFamily: JetBrains Mono
    fontSize: 9px
    fontWeight: '500'
    lineHeight: 12px
    letterSpacing: 0.04em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.06em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 9px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.08em
spacing:
  gutter: 0.5rem
  gutter-sm: 0.25rem
  gutter-lg: 0.75rem
  margin: 0.75rem
  margin-mobile: 0.5rem
  space-xs: 0.125rem
  space-sm: 0.25rem
  space-md: 0.5rem
  space-lg: 0.75rem
  space-xl: 1rem
  space-2xl: 1.5rem
---

## Brand & Style

This design system expresses a high-velocity, sovereign quantitative terminal engineered for institutional derivatives traders, algorithmic funds, and elite retail operators navigating Indian capital markets (NSE/BSE).

The personality balances extreme computational precision with an uncompromising technical command console aesthetic. It evokes absolute operational control, situational awareness, and split-second cognitive clarity under intense volatility. 

The aesthetic is built on:
- **Technical Brutalism meets Cybernetic Minimalism**: Rigid structures, precise low-tolerance grid systems, hair-thin divider boundaries, and non-negotiable data clarity.
- **Ultra-High Data Density**: Maximum viewport utilization, zero ornamental fluff, and optimized eye-scanning paths for complex multi-leg option chains, volatility surfaces, and depth-of-market matrices.
- **Strict Functional Lighting**: Controlled luminescent accents against abyssal carbon surfaces; color indicates real-time delta, momentum, and risk states rather than mere visual decor.

## Colors

The system operates strictly in a deep-space dark mode designed to minimize visual exhaustion during continuous 6.5-hour trading sessions.

### Core Canvas & Structural Tiers
- **Void Base (`#05080D`)**: The foundational canvas layer behind all grid modules and multi-monitor splits.
- **Surface Tier 1 (`#081018`)**: Primary panel containers, chart canvasses, order book backing.
- **Surface Tier 2 (`#0B141D`)**: Nested blocks, module headers, toolbars, and inactive inputs.
- **Surface Elevated (`#101B25`)**: Context menus, hover states, active modals, floating HUD indicators.
- **Structural Lines / Outlines**: Border Low-Contrast (`#16222F`), Border High-Contrast (`#1E293B`).

### Functional Accents & Semantic Signals
- **Primary / Telemetry Aqua (`#00E5FF`)**: Active system focus, execution triggers, live terminal state, strike crosshairs, synthetic strategy overlays. Secondary variant (`#00F5D4`) reserved for volumetric pulses and high-liquidity highlights.
- **Bullish / Yield Flow (`#00E676`)**: Positive return, long open interest, ask-side absorption, call premiums exceeding equilibrium.
- **Bearish / Risk Fracture (`#FF3D57`)**: Negative return, short liquidation, bid drops, put unwinding, margin call warnings.
- **System Hazard / Gamma Warning (`#FFB300`)**: Delta drift, execution slippage warnings, circuit limit alerts, India VIX elevated spikes (>18.00).
- **Subdued Telemetry Slate (`#64748B`) & Bright Muted (`#94A3B8`)**: Labels, column titles, micro-annotations, timestamps, and resting grid lines.

## Typography

The typographic hierarchy enforces absolute structural discipline.

- **Interface Context & Navigation (`Plus Jakarta Sans`)**: Delivers razor-sharp rendering at micro-scales while avoiding the visual fatigue of geometric overshoots. Used strictly for human-readable labels, navigation nodes, system menus, and execution confirmation dialogues.
- **Data Tables, Telemetry & Real-Time Math (`JetBrains Mono`)**: Strict tabular lining figures with zero kerning flutter during millisecond tick-by-tick re-renders. Every financial figure, strike price, PCR value, volume profile, and timestamp renders in JetBrains Mono.
- **Micro-Metric Sizing (`mono-xs` / `9px`)**: Engineered specifically for high-density Greek matrices (Delta, Theta, Gamma, Vega) and order book depths where vertical space dictates information density. All uppercase labels mandate strict character spacing (+0.06em to +0.08em) for instantaneous recognition.

## Layout & Spacing

The terminal is governed by a **Dense Multi-Pane Fluid Mosaic Grid** with strict 4px internal spatial units.

### Modular Tiling Architecture
- **Desktop (Multi-Screen & Ultra-Wide ≥ 1440px)**: 24-column dynamic fluid framework. Tiling windows dock seamlessly with zero outer margins or compact `gutter` (8px). Panels collapse and expand with zero dead space.
- **Laptop / Standard Workstation (1024px - 1439px)**: 12-column adaptive layout. Sub-panels utilize horizontal tabbed stacks to preserve 60fps chart rendering width.
- **Mobile Handheld (320px - 767px)**: Single-column vertical stream. Data tables collapse to fixed primary metric + swipeable Greek metrics. Pinned bottom navigation for rapid order execution triggers.

### Spacing Discipline
Space is viewed as high-value computational real estate. Standard padding rules:
- Table Cells: Vertical padding locked at `space-xs` (2px) to `space-sm` (4px); horizontal padding locked at `space-md` (8px).
- Module Cards: Header padding locked at `space-sm` (4px) to `space-md` (8px); body internal space locked at `space-md` (8px).
- Form inputs: Height locked to dense footprints (24px, 28px, 32px maximum).

## Elevation & Depth

Visual hierarchy is constructed through **Subsurface Tonal Tiering** and **Technical Border Containment** rather than organic blurred drop shadows.

- **Level 0 (Terminal Canvas)**: `#05080D`. Flat, unlit base layer.
- **Level 1 (Docked Modules & Tables)**: `#081018` bordered with `#16222F` (1px solid). No shadow. Visual separation is achieved strictly by contrasting line boundaries.
- **Level 2 (Active Toolbars, Focused Panel, Hovered Row)**: `#0B141D` with high-contrast boundary `#1E293B`.
- **Level 3 (Command Overlays, Quick-Order HUD, Context Panels)**: `#101B25` with an outer 1px structural line `#00E5FF` at 30% opacity, paired with an ambient directed glow: `0 0 16px rgba(0, 229, 255, 0.08)`.
- **Laser Depth Accent**: When a critical state occurs (e.g., automated SL hit or circuit break), the containing card uses an inner edge pulse: `inset 0 0 0 1px #FF3D57`.

## Shapes

The design system enforces **Shape Level 0 (Sharp)** with surgical micro-chamfers on specific telemetry tags.

- **Zero Corner Radius**: All windows, panels, modal dialogs, data cells, charts, tab bars, and order execution buttons have pure `0px` corners. This maintains the unyielding, militaristic data instrumentation aesthetic and optimizes sub-pixel layout alignment across dense screens.
- **Technical Chamfers (Optional Utility Badges)**: Status indicator chips and high-priority flags may utilize a 45-degree corner cut (`clip-path: polygon(...)`) of 3px on the top-right corner to indicate active automated algorithmic scripts.
- **Dividers**: Crisp, 1px single-pixel lines without soft alpha bleeds (`#16222F` resting, `#1E293B` active).

## Components

### Action Triggers (Buttons)
- **Primary / Cyber Accent Button**: Solid `#00E5FF` background, `#05080D` heavy bold text (`headline-sm`), `0px` radius. Minimal height (28px - 32px). Hover switches to secondary aqua `#00F5D4` with a subtle cyan perimeter emission (`0 0 8px rgba(0, 229, 255, 0.4)`).
- **Execution Buy / Long**: Solid `#00E676` background, `#05080D` text. Active state triggers 100ms scale flash.
- **Execution Sell / Short**: Solid `#FF3D57` background, `#FFFFFF` text.
- **Ghost / Utility Action**: Transparent background, 1px solid `#1E293B` border, `#94A3B8` text. Hover changes border to `#00E5FF` and text to `#FFFFFF`.

### Telemetry Badges & Status Chips
- Height: 16px to 20px. Font: `label-sm`.
- **Bullish State**: Background `rgba(0, 230, 118, 0.10)`, text `#00E676`, border `1px solid rgba(0, 230, 118, 0.25)`.
- **Bearish State**: Background `rgba(255, 61, 87, 0.10)`, text `#FF3D57`, border `1px solid rgba(255, 61, 87, 0.25)`.
- **Neutral / Regime State**: Background `rgba(100, 116, 139, 0.12)`, text `#94A3B8`, border `1px solid #1E293B`.

### Quantitative Data Tables (Option Chains & Order Books)
- Column Headers: `label-sm`, uppercase, `#64748B` text, bottom border 1px solid `#1E293B`.
- Row Height: Compact 22px to 26px. Zebra-striping avoided; row separation created via single-pixel dotted borders (`#101B25`).
- Hover State: Full horizontal row highlight with background `#0B141D` and a 2px left-border anchor in `#00E5FF`.
- In-Cell Visualizers: Mini horizontal liquidity volume bars rendered behind numeric values as subtle opacity fills (`rgba(0, 229, 255, 0.08)` for calls, `rgba(255, 61, 87, 0.08)` for puts).

### Inputs & Micro Steppers
- Background `#081018`, border 1px solid `#1E293B`, text `JetBrains Mono` (`mono-md`).
- Focus state: Border instantly shifts to `#00E5FF` without outline offset; cursor changes to a cyan block.
- Embedded stepper buttons (+ / - lots): Square 24px `0px` radius blocks with resting `#64748B` text, turning `#00E5FF` on press.

### Market Depth / DOM Ladders
- Split-column vertical order book ladder. Bid cumulative volume pinned right-aligned in emerald-tinted bars; Ask cumulative volume left-aligned in coral-tinted bars.
- Current Last Traded Price (LTP) bar spans the full column width with solid `#101B25` backing, bright `#00E5FF` tracking outline, and flashing delta micro-arrow.

### Ticker Tapes & Instrument Header Cards
- Fixed top command deck displaying NIFTY 50, BANK NIFTY, SENSEX, and INDIA VIX.
- Continuous tick-flash: Value pulses green (`rgba(0, 230, 118, 0.3)`) or red (`rgba(255, 61, 87, 0.3)`) background highlight for 150ms upon price change, then fades out smoothly to transparent.