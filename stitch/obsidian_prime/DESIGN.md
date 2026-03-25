```markdown
# Design System Specification

## 1. Overview & Creative North Star: "The Sovereign Intelligence"
This design system is engineered to move beyond traditional financial dashboards, pivoting instead toward a high-end, cinematic command center. The Creative North Star, **"The Sovereign Intelligence,"** dictates an interface that feels autonomous and disciplined. 

To break the "template" look, we reject the rigid, flat grid in favor of **intentional asymmetry and depth-based hierarchy**. By utilizing extreme corner radii (up to 48px) and multi-layered glassmorphism, we create an environment where data doesn't just sit on a screen—it floats within a pressurized, obsidian-glass vacuum. The UI should feel like a high-precision instrument: silent, powerful, and ultra-precise.

---

## 2. Colors: Obsidian & Oracle Cyan
The palette is rooted in a high-contrast dark theme, utilizing a "Deep Obsidian" base to ensure the "Oracle Cyan" accents feel like bioluminescent data streams.

### Palette Strategy
- **Primary (`#c3f5ff` / `#00e5ff`):** Reserved strictly for active trading signals, primary actions, and "Oracle" AI insights.
- **Surface Tiers:** We use the `surface-container` scale to define importance. The "Deep Obsidian" base (`surface-lowest`: `#0e0e0e`) acts as the void, while active workspaces rise through the tiers.
- **The "No-Line" Rule:** 1px solid borders are strictly prohibited for sectioning. Boundaries must be defined solely through background color shifts (e.g., a `surface-container-low` module sitting on a `surface` background). 
- **The "Glass & Gradient" Rule:** Floating panels must utilize the glassmorphic effect—`surface-container-high` at 60% opacity with a **40px backdrop blur**. 
- **Signature Textures:** Use a subtle radial gradient transitioning from `primary` to `primary-container` for high-impact CTAs to provide a "pulsing" digital soul.

---

## 3. Typography: Precision & Impact
The typographic pairing reflects the brand's dual nature: the visionary (`Space Grotesk`) and the mathematical (`Roboto Mono` / `Inter`).

- **Display & Headlines (`Space Grotesk`):** High-impact, wide apertures. Used for market regimes, AI confidence scores, and section headers. Use `display-lg` (3.5rem) to create an editorial feel in empty states or hero headers.
- **Data & Precision (`Roboto Mono` / `Inter`):** All numerical trading data, ticker symbols, and timestamps must use `Roboto Mono` (or the precision-mapped `Inter` for body text) to ensure character alignment and rapid scanning.
- **Hierarchy via Scale:** Use extreme contrast between `label-sm` (0.6875rem) for metadata and `headline-lg` (2rem) for primary metrics to establish an authoritative information architecture.

---

## 4. Elevation & Depth: Tonal Layering
In this design system, depth is a functional tool, not a decoration. We replace structural lines with **Tonal Layering**.

- **The Layering Principle:** Stack `surface-container` tiers to create hierarchy. A `surface-container-highest` card should host the most critical real-time data, visually "rising" toward the user.
- **The "Ghost Border" Fallback:** To define depth without clutter, use a **0.5px inner stroke** (Physical Border). Use `white/10` or the `outline-variant` at 15% opacity. This mimics the edge of a polished glass pane.
- **Ambient Shadows:** Shadows are rarely used, but when necessary, they must be "Atmospheric." Use a 64px blur at 8% opacity, tinted with `primary` to suggest the glow of the interface itself.
- **Backdrop Blurs:** Every floating modal or dropdown must use a `40px` blur. This ensures the complex trading background is obscured enough for readability while maintaining the "Cinematic Obsidian" aesthetic.

---

## 5. Components

### Buttons
- **Primary:** Rounded `full` (9999px), `primary-container` background, with a subtle outer glow of `surface-tint`.
- **Secondary:** Ghost variant with the 0.5px "Ghost Border" and `on-surface` text. 
- **Tertiary:** Text-only, using `Space Grotesk` in all-caps `label-md` for a disciplined, military-spec feel.

### Input Fields
- **Styling:** `surface-container-highest` background with a `32px` corner radius. 
- **States:** On focus, the 0.5px border transitions to `primary` (#00E5FF). Use `Roboto Mono` for all numerical inputs to ensure precision.

### Chips & Tags
- **Execution Chips:** Used for "Buy/Sell" status. High-saturation `primary` for Buy, `error` for Sell, using a "pill" shape (`full` radius).

### Cards & Modules
- **Rule:** Forbid divider lines. Separate content using `spacing-8` (2.75rem) of vertical whitespace or by nesting a `surface-container-low` inner block inside a `surface-container-high` card.

### Additional Component: The "Pulse" Indicator
- A microscopic, breathing `primary` dot placed next to live data streams to indicate "Sovereign" AI connectivity.

---

## 6. Do’s and Don’ts

### Do
- **Do** use asymmetrical layouts (e.g., a wide 8-column data visualization paired with a narrow 4-column AI insight panel).
- **Do** lean into extreme roundedness (`xl`: 3rem) for large containers to soften the "institutional" coldness.
- **Do** use `Oracle Cyan` sparingly—it is a laser, not a paint bucket.

### Don't
- **Don’t** use 1px solid borders; they shatter the "glass" illusion.
- **Don’t** use standard "Material Design" shadows. If it doesn't look like light passing through obsidian, it doesn't belong.
- **Don’t** use center-aligned text for data. Accuracy requires the rigid structure of left/right alignment in `Roboto Mono`.
- **Don't** use pure white (`#FFFFFF`) for body text. Use `on-surface` (`#e5e2e1`) to maintain the cinematic high-contrast balance without causing eye strain.