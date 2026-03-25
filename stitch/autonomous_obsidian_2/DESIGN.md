# Design System Strategy: Institutional Futurity

## 1. Overview & Creative North Star
The Creative North Star for this system is **"The Synthetic Oracle."** 

This is not a standard fintech dashboard; it is a high-performance environment where AI-driven autonomy meets institutional authority. The aesthetic rejects the "flatness" of modern SaaS in favor of **Institutional Futurity**—a look that feels like a physical piece of obsidian glass etched with light. 

We break the "template" look by utilizing extreme corner radii (`3rem`) contrasted against a rigid, mathematical grid. By combining the architectural rigidity of **Space Grotesk** with high-precision mono-spaced data, we create a sense of "Engineered Elegance." The layout should feel like a cinematic command center: spacious, dark, and pulsing with silent intelligence.

---

## 2. Colors & Materiality
The palette is rooted in the "Deepest Obsidian" (#050505), layered to create a sense of infinite physical depth.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. They clutter the interface and break the "Oracle" immersion. Boundaries must be defined through:
- **Tonal Shifts:** Placing a `surface-container-low` section against a `surface` background.
- **Glassmorphism:** Using `32px+` backdrop blurs to define interactive regions.
- **Inner Micro-Borders:** A single `0.5px` inner stroke using `outline-variant` at 20% opacity is permitted *only* to catch "specular highlights" on glass edges.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked obsidian plates.
- **Base Layer:** `surface-dim` (#131313) or `surface-container-lowest` (#0e0e0e).
- **Secondary Tier:** `surface-container-low` (#1c1b1b) for large structural areas.
- **Floating/Action Tier:** `surface-container-high` (#2a2a2a) or `highest` (#353534) for active trading modules.

### The "Plasma Glow" Principle
The primary accent `primary_container` (#00E5FF) is never just a flat color. It represents "Data Health." 
- Use **Signature Textures**: Apply a soft radial gradient transitioning from `primary` (#c3f5ff) to `primary_container` (#00e5ff) for primary CTAs to simulate a glowing gas-discharge effect.
- **Glow-as-Data:** A glow is never decorative. The intensity of the blur/spread should correlate to real-time data volatility or system confidence.

---

## 3. Typography
The typography system is an exercise in high-contrast "Architectural Precision."

- **The Display & Headline Scale (`Space Grotesk`):** Used for high-level insights and structural labels. Space Grotesk’s geometric quirks provide the "futuristic" edge. Use `display-lg` (3.5rem) sparingly to anchor the most critical top-level data points.
- **The Data Scale (`Inter` / Tabular Mono):** For trading values, order books, and timestamps, use `Inter` with `tnum` (tabular numerals) enabled. This ensures that fluctuating numbers do not cause horizontal "jitter" in high-speed environments.
- **Visual Hierarchy:** Headlines should be high-contrast (`on_surface`), while secondary metadata should drop significantly in value to `on_surface_variant` to reduce cognitive noise.

---

## 4. Elevation & Depth
Depth is not simulated with drop shadows; it is achieved through **Tonal Layering** and light refraction.

### The Layering Principle
Stacking tokens creates a natural lift. A card using `surface-container-highest` placed on a `surface-container-low` background creates a clear, sophisticated hierarchy without a single pixel of "ink."

### Ambient Shadows
If a component must "float" (e.g., a critical alert or dropdown), use a shadow with a `24px` to `48px` blur radius, set to `4-8%` opacity. The shadow color must be a tinted version of `surface_tint` (#00daf3) to simulate the way cyan light would bleed into the surrounding obsidian.

### Glassmorphism & Ghost Borders
- **Blur:** Minimum `32px` backdrop-filter.
- **Ghost Border:** If an edge needs definition for accessibility, use `outline` (#849396) at `15%` opacity. This should look like a faint reflection on a glass edge, not a stroke.

---

## 5. Components

### Buttons
- **Primary:** `primary_container` background with a subtle "plasma" outer glow (4px blur, same color). Text is `on_primary`. Corner radius: `full`.
- **Secondary (The Glass Button):** Transparent background, `32px` backdrop blur, and a `0.5px` ghost border. 
- **Tertiary:** No background or border. `primary_fixed_dim` text.

### High-Precision Data Cards
Forbid all divider lines. Use `spacing-6` (2rem) of vertical white space to separate data clusters. 
- **Header:** `headline-sm` in `Space Grotesk`.
- **Body:** `body-md` in `Inter` with `surface-container-lowest` background to "recess" the data into the page.

### Inputs & Selectors
- **Input Fields:** Use `surface-container-lowest` with an inner shadow to create a "carved" look. Corner radius: `1rem` (md).
- **Active State:** The border glows softly with `primary_fixed_dim`.

### Specialized Components: "The Oracle Pulse"
- **Status Indicator:** A pulsing dot using `primary_container`. The pulse's rhythm should sync with the API heartbeat.
- **The Precision Sparkline:** A 1px line using `primary` that leaves a fading "trail" of `primary_container` glow.

---

## 6. Do's and Don'ts

### Do
- **Do** use generous spacing (`spacing-12` or `spacing-16`) between major modules to allow the "Institutional" scale to breathe.
- **Do** use `xl` (3rem) corner radii for main containers to achieve the "Soft-Tech" organic feel.
- **Do** align all text to a strict mathematical grid, even if the container shapes are fluid.

### Don't
- **Don't** use 100% white (#FFFFFF). Use `on_surface` (#e5e2e1) to maintain the cinematic dark-mode tonality.
- **Don't** use sharp 90-degree corners. Even "rigid" elements should have a minimum `sm` (0.5rem) radius.
- **Don't** use "Standard" drop shadows. They look muddy on obsidian surfaces; use tonal layering instead.
- **Don't** use more than one "Plasma Glow" element per viewport. If everything glows, nothing is important.