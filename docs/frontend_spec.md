# KG Community Recovery Portal: Frontend Design Specification

## 1. The Vibe: Tech-Centric & Professional

The portal must feel like a modern, high-trust SaaS application or a clean Idea Submission Portal. We are moving away from basic, unstyled forms toward a structured, card-based dashboard layout.

**Core Aesthetics:**
*   **Structured Layout:** Information should be framed in discrete, soft-shadowed cards against a slightly tinted background to create depth.
*   **Sidebar Navigation:** A permanent left-hand sidebar for primary navigation (Dashboard, Feed, My Reports, Settings), leaving the main content area focused and wide.
*   **Status-Driven:** Immediate visual identification of an item's state via clear, distinct badge colors.
*   **Typography:** Clean, sans-serif fonts (e.g., Inter or Roboto). High contrast for data points, muted tones for metadata.

## 2. Color Palette & UI Framework

We will stick with **Bootstrap 5** to maintain velocity with our existing Django/Crispy Forms integration, but we will deeply customize the SCSS variables to achieve a "Tailwind-like" modern aesthetic.

**Custom Color Scheme (Deep Blues & Slate Greys):**

*   **Primary Accent (`--bs-primary`):** `#1E40AF` (Deep Royal Blue) - Used for primary actions, active state links, and important highlights.
*   **Secondary Accent (`--bs-secondary`):** `#64748B` (Slate Grey) - Used for secondary buttons, less critical icons.
*   **Background (`--bs-body-bg`):** `#F8FAFC` (Very Light Slate) - Creates a soft contrast against pure white cards.
*   **Surface/Cards (`--bs-card-bg`):** `#FFFFFF` (Pure White) - With a subtle, large-radius box shadow (`box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1)`).
*   **Text Primary (`--bs-body-color`):** `#0F172A` (Near Black/Very Dark Slate) - For high legibility.
*   **Text Muted:** `#64748B` (Slate Grey) - For dates, helper text.

**Status Badge Colors (The "Data Display" Rule):**
*   **Lost (`--bs-danger`):** `#EF4444` (Soft Red) - Urgent, needs attention.
*   **Found (`--bs-success`):** `#10B981` (Emerald Green) - Positive, item secured.
*   **Pending/Handover (`--bs-warning`):** `#F59E0B` (Amber) - Transition state.
*   **Resolved/Claimed (`--bs-info`):** `#3B82F6` (Bright Blue) - Final, neutral state.

## 3. Component Breakdown

To build the "Portal" aesthetic, the junior team needs to focus on these core, reusable components:

### A. The Sidebar Layout
A fixed left sidebar containing the logo, user profile snippet, and primary navigation links. The active link should have a primary-colored left border and light blue background tint.

### B. Action Header
The top of every main content area should have a title, an optional subtitle, and primary call-to-action buttons (e.g., "Report Item") aligned to the right.

### C. The Item Card (Grid Component)
The fundamental building block of the feed. It must be a uniform size, handle images gracefully, and present complex data cleanly. (See detailed brief below).

### D. The Status Badge
A standardized pill-shaped badge component used uniformly across feeds, detail views, and tables.

### E. Handover / Multi-Step Form Layout
For complex actions like the "Handover" process (verifying ownership and transferring an item), we will use a **modal or an accordion-style conditional UI**. 
*   **UX Rule:** Do not show the handover verification fields on the main detail view. They should only appear after clicking a "Initiate Handover" action button, expanding a clean, focused form area below to prevent clutter.

## 4. Junior Dev Brief: The Item Card Component

**Ticket:** Build the Reusable Item Card Component
**Context:** We need a standardized "Card" to display Lost/Found items in our grid feeds. It needs to look like a modern SaaS dashboard widget.

**Requirements:**
1.  **Structure:** Use a Bootstrap `.card` with `.h-100` for equal heights in the grid. Remove the default border (`.border-0`) and add our custom soft shadow (`.shadow-sm`). Round the corners slightly more than default.
2.  **Image Area:**
    *   Top of the card. Fixed height (e.g., `200px`).
    *   Must use `object-fit: cover;` so images don't stretch or distort.
    *   Fallback: If no image exists, display a solid light grey rectangle (`#E2E8F0`) with a centered, muted Bootstrap Icon (`bi-image`).
3.  **Status Badge (Crucial):**
    *   Must be absolutely positioned *over* the top-right corner of the image, OR prominently placed at the very top of the card-body.
    *   Use the defined Badge colors (Red for Lost, Green for Found). Use `.rounded-pill`.
4.  **Content Area (`.card-body`):**
    *   **Title:** `.fw-bold`, `.text-truncate` (prevent long titles from breaking the layout). Dark slate text.
    *   **Location:** Below the title. Use a small location pin icon (`bi-geo-alt`). Text color: Muted slate.
5.  **Footer Area (`.card-footer`):**
    *   `.bg-transparent` and `.border-top-0` to keep the layout clean.
    *   Left side: Date reported (Muted small text).
    *   Right side: "View Details" button. Use an outline button (`.btn-outline-primary`) or a subtle icon button (an arrow pointing right) to keep it minimal.
    
**Target HTML Structure Example:**
```html
<div class="card h-100 border-0 shadow-sm custom-rounded">
    <!-- Image Area -->
    <div class="position-relative">
        <img src="..." class="card-img-top item-image" alt="...">
        <!-- Absolute position badge over image -->
        <span class="badge bg-danger position-absolute top-0 end-0 m-3 rounded-pill shadow-sm">LOST</span>
    </div>
    <!-- Body -->
    <div class="card-body">
        <h5 class="card-title fw-bold text-truncate text-slate-dark">Macbook Pro 16"</h5>
        <p class="card-text text-muted small"><i class="bi bi-geo-alt"></i> Main Library, 2nd Floor</p>
    </div>
    <!-- Footer -->
    <div class="card-footer bg-transparent border-0 d-flex justify-content-between align-items-center">
        <small class="text-muted">2 hours ago</small>
        <a href="#!" class="btn btn-sm btn-outline-primary rounded-pill px-3">View</a>
    </div>
</div>
```
