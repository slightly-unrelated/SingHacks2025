## Design Style of Julius Baer — Overview

![Image](https://www.projectcrux.design/assets/images/casestudy/sophisticated1.webp)

![Image](https://logotyp.us/file/julius-bar.svg)

![Image](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Julius_B%C3%A4r_Logo.svg/2560px-Julius_B%C3%A4r_Logo.svg.png)

Here’s a breakdown of the key visual/UI design characteristics of Julius Baer’s website and brand — this should help you design your application in a matching style.

---

### 1. Branding & Colour Palette

* The logo uses a **serif typeface**, which suggests heritage, stability and trust.
* Primary colours appear to be: a deep navy-blue (or almost charcoal blue) + white + generous whitespace.
* Accent colour (for links/buttons) appears lighter/medium blue or subtle grey.
* Overall palette is restrained; luxury / premium feeling rather than bright or playful.
* Use of high-quality photography (artful, lifestyle/wealth-management context) to reinforce premium brand.
* Whitespace and minimal distraction: the site feels spacious and calm.

**Design implication for your app:**

* Use the navy-blue as primary UI theme (header, key buttons), white or very light backgrounds.
* Avoid overly bright or saturated colours; keep accents subtle.
* Use serif font for headings maybe (to evoke the tradition) and a clean sans-serif for body text.
* Use luxury-style photography where appropriate (hero images, context).
* Maintain generous padding/margins: feel of “premium”.

---

### 2. Typography & Text Style

* Headings: look clean, clear, with good letter-spacing; large enough to create hierarchy.
* Body: readable, comfortable line-height, not too dense.
* Emphasis: Use subtle weights changes rather than heavy glows or shadows.
* Tone: Professional, calm, authoritative — the text doesn’t shout, it informs.

**Design implication:**

* Choose a serif for headings (e.g., “Merriweather”, “Playfair Display”) and a clean sans-serif for body (e.g., “Roboto”, “Inter”).
* Use clear hierarchy: H1 large, H2 medium, body standard; ensure mobile readability.
* Avoid overly decorative fonts or gimmicks.

---

### 3. Layout & UI Structure

* The website favours large hero sections, clean grids, generous whitespace.
* Navigation is top-bar, minimal; content sections are well separated.
* Imagery often full-width or large cards with subtle overlays.
* Responsive behaviour: likely adapts gracefully, though the desktop view emphasises space and calm.

**Design implication:**

* In your application, establish a clear layout: header nav, main content area, perhaps side panel if needed but keep it light.
* Use cards or list views with good spacing.
* For dashboards or analytics (your AML system) keep UI clean: metal lines, subtle shadows, good whitespace.
* Avoid clutter: since Julius Baer’s brand is premium, you want your app to feel *refined* not overloaded.

---

### 4. Iconography & UI Elements

* Icons, if used, seem minimal and line-based rather than heavy/filled.
* Buttons: likely flat/solid, with subtle hover states, no heavy gradients or flashy animations.
* Illustrations/photos: mostly real-world photography rather than cartoon/flat-illustration style.

**Design implication:**

* Use line or minimalist icons (e.g., “feather icons”, “heroicons”) in UI.
* Buttons: primary solid (navy blue on white), secondary outline maybe, hover states subtle.
* Use real photography for hero images or dashboards background (wealth context) if needed, but keep analytics/screens more abstract and data-centric (so as not to detract from functionality).

---

### 5. Tone & UX Feel

* The brand feels: **luxury, stable, mature, globally-aware**.
* UX: calm, confident, not rushed, letting the user digest.
* No gimmicks, animations are subtle if present, focus is on clarity and trust.

**Design implication:**

* When designing alerts, dashboards and workflows (your AML system), maintain the tone: serious but approachable.
* Use subtle transitions/animations only where they add clarity (e.g., alert slide-in) not for decoration.
* For role-specific views: keep consistency in structure, colours, typography, so the experience feels like part of the Julius Baer brand.

---

### 6. Application of Style to Your AML System

Since you’re building an internal/hybrid system (for Compliance/Front-Office/Legal) aligned to Julius Baer style, some specific recommendations:

* **Dashboard header:** navy background, white Julius Baer branded logo + app name (e.g., “AML Monitor”).
* **Sidebar nav (if present):** dark background (#1b2b3d type navy) with white icons and text. On hover, accent (lighter blue).
* **Main content area:** white background (#fff) with generous padding, cards with subtle shadow (#e6e8ec) or border.
* **Risk score visuals:** use the brand accent blue for normal/medium; for high risk maybe use a dark navy/red? But avoid too bright red — maybe a deep burgundy consistent with luxury palette.
* **Alerts list:** use card style or table with row hover, light accent highlight for high priority.
* **Typography:** Headings (serif) e.g., “Playfair Display”, body text (sans) e.g., “Inter”.
* **Colours example palette:**

  * Primary navy: `#1B2B3D`
  * Accent blue: `#0066CC`
  * White: `#FFFFFF`
  * Surface grey: `#F5F7FA`
  * Text dark: `#333333`
  * Risk high accent: maybe `#A30000` (deep but muted)
* **Icons:** Use simple line icons in navy or grey; if used filled icons, keep them monochrome.

---

### 7. Visual References

![Image](https://www.juliusbaer.com/fileadmin/_processed_/a/0/csm_Holistic_wealth_hub_a0a01d43c0.png)

![Image](https://img.hubbis.com/optimiser/img/news/cropped/8288d56e2b164f912d3959b3ec439a0dc0eec07f.png)

![Image](https://www.juliusbaer.com/fileadmin/_processed_/8/9/csm_juliusbaer-homepage-hero-q4_416c0645da.jpg)

![Image](https://www.juliusbaer.com/fileadmin/_processed_/2/c/csm_wealth-hero_11f5304f79.jpg)

![Image](https://mir-s3-cdn-cf.behance.net/projects/404/96d7c8182911875.Y3JvcCw4MDgsNjMyLDAsMA.jpg)

![Image](https://mir-s3-cdn-cf.behance.net/projects/404/17f65b233286103.Y3JvcCw5MjAsNzIwLDc5LDA.jpg)

Use these as reference while designing your UI: notice how large imagery, generous space, calm colours work together.

---

If you like, I can **extract key CSS/brand tokens** (colours, font sizes, spacing) from the Julius Baer site (via developer tools) and produce a mini “style-guide” snippet (SCSS or CSS-variables) you can directly use as foundation for your app. Would that be helpful?
