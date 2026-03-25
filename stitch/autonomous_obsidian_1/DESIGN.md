# Design System Specification: Institutional Futurity

## 1. Overview & Creative North Star: "The Obsidian Engine"
The Creative North Star for this design system is **"The Obsidian Engine."** In the world of high-frequency algorithmic trading, speed is invisible, and precision is absolute. We are moving away from the cluttered, "dashboard-heavy" aesthetic of traditional fintech. Instead, we embrace a cinematic, editorial approach that feels like a high-end physical installation.

This system rejects the "web-template" look by utilizing **Intentional Asymmetry** and **Monolithic Layering**. We use the void (deep blacks) not as empty space, but as a structural element that pushes the most critical financial data into the foreground. Layouts should feel like a coordinated HUD—precise, authoritative, and calm under pressure.

---

## 2. Colors: High-Contrast Luminance
We utilize a core palette of deep charcoals and blacks to ground the experience, allowing our "Status Glows" to guide the eye through complex data sets.

### Core Palette (Material Design Mapping)
*   **Background / Surface:** `#131313` (The Void)
*   **Primary (Cyan Info):** `#c3f5ff` | Container: `#00e5ff`
*   **Tertiary (Emerald Success):** `#9cffe4` | Container: `#55e7c6`
*   **Error (Sharp Red):** `#ffb4ab` | Container: `#93000a`
*   **Secondary (Neutral/Ghost):** `#c6c6c9`

### The "No-Line" Rule
**Borders are strictly prohibited for sectioning.** To define boundaries, you must use background shifts. A `surface-container-low` component should sit on a `surface` background. The eye should perceive change through tonal depth, not 1px mechanical strokes.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, obsidian-like plates:
1.  **Base Layer:** `surface-container-lowest` (#0e0e0e) for the deep background.
2.  **Primary Content Areas:** `surface` (#131313).
3.  **Interactive Cards/Modules:** `surface-container` (#201f1f).
4.  **Floating Modals/Popovers:** `surface-bright` (#3a3939).

### The Glass & Gradient Rule
For high-priority UI elements (like active trade executions), use **Glassmorphism**. Apply a semi-transparent `primary-container` color at 10% opacity with a `24px` backdrop-blur. Use a linear gradient (`primary` to `primary-fixed-dim`) at a 45-degree angle for primary CTAs to give them a "machined" metallic finish.

---

## 3. Typography: Precision Engineering
Our typography choice reflects the dual nature of the brand: Futuristic Vision and Mathematical Rigor.

*   **Display & Headlines:** **Space Grotesk.** This font provides a technical, mono-linear feel that suggests algorithmic logic.
    *   *Usage:* Use `display-lg` (3.5rem) for macro-data or key KPIs. Use `headline-sm` (1.5rem) for module titles.
*   **Body & Numerals:** **Inter.** Chosen for its exceptional legibility at small scales. 
    *   *Usage:* All financial tables and data grids must use Inter with tabular-numeral OpenType features enabled to ensure decimal alignment.
    *   *Hierarchy:* Use `body-md` (0.875rem) for standard text; `label-sm` (0.6875rem) in uppercase with 10% letter spacing for technical metadata.

---

## 4. Elevation & Depth: Tonal Layering
We do not use drop shadows to simulate "light." We use them to simulate "glow" or "ambient occlusion."

*   **The Layering Principle:** Depth is achieved by "stacking." A `surface-container-high` card placed on a `surface-container-low` section creates a natural lift.
*   **Ambient Shadows:** For floating elements, use a "Ghost Glow." Instead of black shadows, use a diffused `primary` or `on-surface` tint at 4% opacity with a 40px blur.
*   **The "Ghost Border" Fallback:** If a UI element (like a search input) risks disappearing, use a "Ghost Border": `outline-variant` (#3b494c) at **15% opacity**. Never use 100% opacity borders.
*   **Hard Edges:** Note the **0px Radius Scale**. This design system is Brutalist and Institutional. Every corner is a sharp 90-degree angle, emphasizing precision and "no-nonsense" engineering.

---

## 5. Components

### Buttons: High-Stakes Interaction
*   **Primary:** Sharp 90° corners. Background is a gradient of `primary` to `primary-container`. Text is `on-primary` (Deep Teal).
*   **Secondary:** Ghost variant. No background, only a "Ghost Border" (15% opacity `outline`). On hover, the background fills to 5% `primary` opacity.
*   **Tertiary:** Text-only, `label-md` style, uppercase with 0.1rem letter spacing.

### Data Inputs: The Command Line
*   **Text Fields:** No bottom line. Use `surface-container-highest` as the background fill. The active state is indicated by a 2px left-side accent bar in `primary` (Cyan).
*   **Checkboxes/Radios:** Use sharp squares. When active, use a "Glow" effect—the `primary` color should appear to emit light into the surrounding pixels.

### Cards & Lists: Editorial Grouping
*   **Rule:** **Forbid Divider Lines.** Use the Spacing Scale (specifically `spacing-8` or `spacing-12`) to create "Active Negative Space." 
*   **The "Algorithm" List:** List items should use a subtle background transition on hover (from `surface` to `surface-container-low`) to indicate interactivity.

### Specialized Component: The Pulse Indicator
*   For active algorithmic trades, use a 4px dot of `tertiary` (Emerald) with a CSS animation that ripples a 20% opacity circle outwards. This provides "System Life" without distracting from the data.

---

## 6. Do’s and Don’ts

### Do:
*   **Use Asymmetric Grids:** Allow one column to be significantly wider than others to create an editorial, "Portfolio" feel.
*   **Embrace the Dark:** Keep 80% of the UI in the `surface` to `surface-container-lowest` range.
*   **Tabular Figures:** Always ensure financial data is monospaced for vertical scanning.

### Don’t:
*   **No Rounded Corners:** Do not use `border-radius`. Ever. It breaks the "Institutional" authority of the system.
*   **No Generic Grays:** Do not use #888888. Use our `on-surface-variant` (#bac9cc) which is tinted with cyan to keep the "cinematic" temperature cool.
*   **No Clutter:** If a piece of data isn't actionable or vital, move it to a `label-sm` secondary view. Space is luxury.