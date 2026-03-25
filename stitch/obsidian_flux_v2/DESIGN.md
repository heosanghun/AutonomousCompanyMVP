# The Design System: Institutional Intelligence & Cinematic Depth

## 1. Overview & Creative North Star: "The Synthetic Oracle"
This design system is engineered to bridge the gap between high-frequency institutional trading and the avant-garde aesthetic of autonomous AI. The Creative North Star is **"The Synthetic Oracle"**—a visual language that feels omniscient, calm, and hyper-precise. 

We reject the "SaaS-standard" dashboard. Instead, we embrace **Aero-Dynamic Layering**: a methodology where the interface feels like a series of glass HUD elements floating in a deep obsidian void. By utilizing intentional asymmetry—such as offset data visualizations and overscaled headline typography—we break the rigid "template" feel, replacing it with an editorial sophistication that commands authority.

---

## 2. Color & Surface Architecture
The palette is rooted in `surface` (#131314), moving away from flat blacks into a "Deep Obsidian" spectrum.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. Structural definition must be achieved through:
1.  **Tonal Shifts:** Moving from `surface_container_lowest` to `surface_container_high`.
2.  **Aero-Dynamic Depth:** Using `backdrop-blur` (30px+) on glass elements.
3.  **Inner Glows:** Using a 1px inner-border with 10% opacity white to define edges against dark backgrounds.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack. The deeper the information, the darker the surface:
*   **Base Layer:** `surface` (#131314) - The infinite void.
*   **Sectioning:** `surface_container_low` (#1C1B1C) - Defining broad regions.
*   **Actionable Cards:** `surface_container_highest` (#353436) - Bringing critical data forward.
*   **Glass Overlays:** Semi-transparent `primary_container` (#00E5FF at 8% opacity) with heavy blur for modal states.

### Neon Soul (The Signature Texture)
Main CTAs and critical AI insights should utilize a "Neon Soul" gradient. Transition from `primary` (#C3F5FF) to `primary_container` (#00E5FF) with a 2px outer glow of the same hue at 20% opacity. This provides a "powered-on" digital pulse that flat colors cannot replicate.

---

## 3. Typography: The Editorial Edge
We pair the technical precision of a trading floor with the bold presence of a high-end journal.

*   **Display & Headlines (Space Grotesk):** Use `display-lg` and `headline-lg` for high-level AI insights and portfolio totals. The futuristic, wide stance of Space Grotesk creates an immediate sense of "The Future of Finance." Use **Tight Tracking (-2%)** for headlines to increase visual density.
*   **Data & Logistics (Inter / Roboto Mono):** All tabular data and execution logs must use `body-md` or `label-sm`. Roboto Mono is reserved for price tickers and transaction hashes to ensure character alignment.
*   **Visual Hierarchy:** Establish authority through scale. A `display-lg` portfolio balance should sit in stark contrast to `label-sm` secondary metrics, creating a clear entry point for the eye.

---

## 4. Elevation & Depth: Tonal Layering
We avoid traditional drop shadows which feel "muddy" in dark mode. 

*   **The Layering Principle:** Place a `surface_container_lowest` element inside a `surface_container_high` wrapper to create a "recessed" look, or vice versa for a "raised" look.
*   **Ambient Shadows:** For floating elements (Modals/Popovers), use an extra-diffused shadow: `offset-y: 24px, blur: 48px, color: rgba(0, 229, 255, 0.06)`. This tints the shadow with our "Neon Cyan," simulating light emission from the UI itself.
*   **The Ghost Border:** If a boundary is required for accessibility, use the `outline_variant` token at **15% opacity**. It should be felt, not seen.

---

## 5. Components: Precision Primitives

### Buttons & Interaction
*   **Primary (AI/Intel):** Background: `primary_container` (#00E5FF); Text: `on_primary` (#00363D). Apply a subtle 4px blur glow on hover.
*   **Secondary (Execution):** Ghost style. `outline` border at 20% opacity, transitioning to 100% on hover.
*   **Tertiary:** Text-only using `primary_fixed` color.

### Aero-Dynamic Cards
*   **Radius:** Strict `lg` (2rem / 32px) for outer containers; `md` (1.5rem / 24px) for nested inner elements.
*   **Styling:** No solid background. Use `surface_container_low` at 80% opacity with `backdrop-filter: blur(30px)`.

### Data Visualization (The "Trading Ticker")
*   **Success:** `secondary` (#4EDE93) for "In-Profit" states.
*   **Risk:** `tertiary_container` (#FFC1BC) for "Critical Exposure."
*   **Spacing:** Use the 8px grid (Token `4` = 0.9rem) religiously to separate data points. Never use dividers; use white space.

### Inputs & Fields
*   **State:** Default state uses `surface_container_highest`. Active/Focus state triggers a `primary` (#C3F5FF) "Ghost Border" and a subtle cyan inner glow.
*   **Validation:** Error states use `error` (#FFB4AB) with a soft crimson pulse animation.

---

## 6. Do’s and Don’ts

### Do:
*   **DO** use asymmetric layouts. For example, align a headline to the far left and the data-grid to the right, leaving a "void" in the center-top.
*   **DO** ensure all text on glass surfaces uses `on_surface` or `on_background` to exceed WCAG AA contrast.
*   **DO** use `9999px` (full) roundedness for status chips, but keep cards at `lg` (2rem).

### Don't:
*   **DON'T** use 100% opaque, high-contrast borders between sections. It kills the cinematic immersion.
*   **DON'T** use standard grey shadows. Shadows should always be a low-opacity tint of the surface or primary color.
*   **DON'T** clutter the viewport. If a metric isn't "Institutional-Grade" essential, hide it behind a progressive disclosure pattern.