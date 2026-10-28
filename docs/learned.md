# Learned Concepts (docs/learned.md)

## PgBouncer Transaction Pooling & Prepared Statements
- Connection poolers reuse backend connections across multiple clients, conflicting with persistent server-side prepared statements.
- Analogy: A shared restaurant kitchen where chefs cannot leave unlabeled personal spice containers on the shared counter between shifts.

## Thin Client Architecture for Bots
- Isolates user interface interactions in the bot while centralizing domain logic, database operations, and validation inside the backend API.
- Analogy: An ATM machine that only captures pin entries and requests cash from the centralized bank vault server.

## N+1 Query Anti-Pattern
- Occurs when an application retrieves one primary record list, then issues individual queries for each child relationship.
- Analogy: A delivery courier traveling back and forth to the warehouse for each individual package instead of loading the entire van at once.

## Safe Migration Splitting in Asyncpg
- Asyncpg enforces strict protocol compliance requiring single statement executions per network exchange.
- Analogy: Passing individual items through a security scanner one by one rather than pushing an entire baggage stack simultaneously.

## Eliminating Swallowed Exceptions (Observability)
- Swallowing errors with bare `pass` conceals underlying defects, blinding telemetry and health metrics.
- Analogy: Disconnecting the "Check Engine" light in a car instead of diagnosing the spark plug, making engine failure undetectable.

## Direct Identifiers & Bridge UX (Media Kodlari)
- Displaying short, persistent codes on web items eliminates fuzzy search ambiguity when users transition to external thin clients (e.g., Telegram bots).
- Analogy: An airport baggage claim tag number that matches your physical suitcase directly, avoiding the need to open every brown bag to identify yours.

## Information Architecture & Cognitive Ergonomics (Hick's Law)
- Reducing sprawling, dead, or duplicate menu hierarchies into a focused set of primary routes minimizes decision fatigue and speeds up user navigation.
- Analogy: A fine dining menu with 8 curated courses versus a chaotic 40-page binder of mismatched dishes where half the ingredients are out of stock.




## Split Card Architecture & Progressive Disclosure
- Separating the media poster container from textual labels (title, subscription status) while revealing detailed ratings and metadata exclusively on hover keeps catalog grids clean, uncluttered, and highly readable.
- Analogy: A book cover in a bookstore where the title and publisher badge are clearly visible on the spine, but flipping to the back blurb reveals reviews and detailed edition data.

## GPU Hardware-Accelerated Infinite Marquee (CSS translate3d)
- Continuous ticker animations using CSS `translate3d` bypass CPU JavaScript rendering and execute directly on the GPU compositor thread, guaranteeing 60/120 FPS without draining device batteries or causing frame stutter.
- Analogy: An airport baggage carousel moving effortlessly on its mechanical motor track rather than airport staff physically carrying each luggage bag around the room by hand.

## Glassmorphic Translucency & Visual Noise Reduction
- Removing repetitive metadata pills (such as `#CODE` or `SERIAL`) from movie card surfaces eliminates visual clutter, allowing the authentic cinema poster art to capture full user attention.
- Analogy: Removing price tags and inventory barcode stickers from the front of art exhibition paintings, so viewers enjoy the pure painting.

## Mobile Header Concision & Touch Target Ergonomics
- Overly verbose headings on mobile screens cause awkward line breaks that push actual media content below the fold. Shortening titles and ensuring touch targets are at least 44x44px preserves screen real estate and makes navigation effortless on touchscreens.
- Analogy: Highway road signs that use concise, punchy text ("Aeroport 2 km") instead of lengthy paragraphs, allowing drivers to read instantly without slowing down.

## 3-Column Mobile Catalog Density (Visual Throughput)
- Moving from 2 columns to 3 columns on mobile screens increases content density by 50%, enabling users to scan 6 to 9 movie options per screen fold without excessive finger scrolling.
- Analogy: A supermarket shelf displaying 3 neatly organized products across each rack rather than 2 oversized boxes, making browsing faster and choices clearer.

## DRY & Single Source of Truth for Media Cards
- Reusing a single unified `MovieCard` component across home page sliders, category rows, and catalog grids eliminates duplicated CSS/markup and prevents design drift.
- Analogy: Standardizing on an official national passport template so all embassies and checkpoints issue and recognize identical formats without regional inconsistencies.

## Hydration State Guard & LocalStorage Persistence
- Guarding client-side synchronization effects with an initialization flag prevents default initial state values from prematurely wiping persistent user preferences on page refresh (F5).
- Analogy: Checking whether an office is already occupied before turning off the light switch at the doorway, preventing you from accidentally plunging someone into darkness.

## Zero-Mock Integrity & Visual Artifact Pruning
- Purging synthetic pseudo-elements (like artificial stack lines or fake metadata pills) ensures the card matches pure production data and removes distracting UI noise.
- Analogy: Removing decorative imitation plastic wraps from a sleek glass smartphone case so only the authentic clean finish remains.

## Parent Entity Resolution from Child Identifiers (Fallback Routing)
- Resolving parent entities (e.g., serial or movie) directly from episode codes or child IDs prevents 404 dead ends when users deep-link from watch history or notifications.
- Analogy: Presenting an individual train ticket stub at the station gate, and the terminal instantly identifying and displaying the full scheduled express train route.

## Horizontal Filter Bar & Instant Micro-Interactions
- Surfacing filter dimensions (genres, countries, ratings, years) directly on a persistent single-line horizontal bar with toggle chips eliminates multi-click accordion fatigue.
- Analogy: The intuitive physical radio preset buttons on a car dashboard that let drivers switch channels with one tap instead of digging through a deep touchscreen settings menu.

## Asynchronous Metadata Enrichment for Unified Templates
- Fetching missing parameters asynchronously on component mount enriches incomplete legacy client-side records up to standard template schema without breaking backwards compatibility.
- Analogy: Scanning an old paper library card at the counter, and the computer instantly printing out the updated digital barcode and full book catalogue details onto it.

## Progressive Tabbed Disclosure for Media Episodes
- Condensing multi-season episodes into tabbed selectors and compact responsive tiles eliminates vertical screen scroll clutter and accelerates episode selection on mobile.
- Analogy: A compact binder with tabbed dividers where you flip directly to Chapter 2 instead of unrolling a 50-meter paper scroll on the floor.

## Unified Metadata Container & Drag-to-Scroll Slider
- Combining team credits and production facts into a single unified container with mouse drag and chevron buttons provides frictionless horizontal exploration on desktop.
- Analogy: An interactive digital museum display where you can swipe through portraits with your finger or mouse, with all historical artifact details gathered neatly on the lower plaque.

## Watchlist-Driven Subscriptions (Favorite Notifications)
- Redefining subscriptions as personal content favorites empowers users to track ongoing series and franchises with smart push notifications instead of paywall gates.
- Analogy: Subscribing to your favorite YouTube channel or podcast to get notified when the next episode drops, without needing to pay upfront.

## Catalog Cross-Referencing & Demand Generation Loop
- Cross-referencing external actor filmography against the local catalog separates available items for immediate streaming from missing titles eligible for one-tap requests.
- Analogy: Looking up an author's complete works at a bookstore, where available books are pulled from the shelf and missing ones can be backordered with a single slip.

## Faceted Taxonomy for Collections & Chronologies
- Segmenting curated media collections into Themes, Franchises, and Chronologies prevents cognitive clutter and guides viewers through intricate cinema timelines.
- Analogy: A library dividing historical sagas into general topics, universe series, and exact chronological timelines so readers know which book to open first.

## Multi-Strategy Entity Resolution & Local Enrichment Persistence
- Resolving heterogeneous identifiers (ID, code, or child episode code) and immediately syncing full metadata into local storage prevents broken fallback cards.
- Analogy: A postal worker who figures out a resident's street address from an incomplete parcel code and updates the delivery ledger so future mail arrives without delay.

## Ambient Video Backdrop & Vignette Layering
- Stacking an auto-looping muted video behind high-contrast gradient masks preserves instant LCP poster loading while providing an immersive cinematic backdrop without obscuring metadata.
- Analogy: A movie cinema foyer where dynamic preview footage quietly rolls on the wall behind the poster standee without overpowering the schedule board.

## Scroll-Snap Container Padding vs. Snapport Alignment
- Placing padding on the outer static wrapper rather than the inner scroll-snapping container prevents multi-item carousels from snapping past the padding and sticking to the screen border.
- Analogy: A display case where the velvet border surrounds the whole shelf, rather than moving along with the sliding glass door and falling off the edge.

## Linear Migration Upgrades & Schema Synchronization
- Applying pending Alembic migrations linearly ensures tables match application models without dropping connections or breaking client queries.
- Analogy: Upgrading the electrical wiring and outlets of an apartment room by room using standard certified blueprints without switching off power to the entire building.

## Server-Side Pre-fetching & Hydration Resilience
- Pre-fetching critical component data on the server during initial render guarantees complete HTML delivery even when client-side script chunks experience network latency.
- Analogy: Buying a fully assembled bicycle directly from the store rather than receiving loose parts in a box with missing wrenches that prevent you from riding.

## Curated Seed Cache with Dynamic Search Fallback
- Serving popular entities from a verified local seed provides instant sub-millisecond responses while transparently querying upstream APIs when users explore long-tail items.
- Analogy: A barista who keeps the 40 most requested specialty coffee blends ready in transparent jars on the front counter, while grinding rare single-origin beans on-demand from the back pantry when a customer orders them.

## Contextual Deep Discovery & Intentional Drag Filtering
- Distinguishing intentional tap/click actions from scroll swipes allows horizontally slidable media carousels to trigger deep-dive modal filmographies without accidental popups.
- Analogy: Flipping through vinyl records in a music crate by gliding your hand along the tops, and only pulling out an album cover when your finger deliberately taps on a specific record sleeve.

## Mobile Density Scaling & Visual Information Throughput
- Scaling down avatar circles (`w-16`), shortening vertical padding, and switching to a 3-column responsive layout doubles on-screen information density on mobile phones without sacrificing touch legibility.
- Analogy: A compact contact list in a smartphone phonebook with neat circular thumbnails instead of giant full-screen business cards that require endless scrolling.

## In-Place Expanding App Bar (Mobil qidiruv animatsiyasi)
- Temporarily cross-fading primary branding and action controls with a full-width search input on mobile viewports maximizes typing area and focus without permanently crowding the top navigation bar.
- Analogy: A compact luxury train dining table that smoothly unfolds when you are ready to eat, and folds flat into the wall once you are done so the passage remains clear.

## Smart Idle Inactivity Transition & Cinema Mode
- Auto-fading foreground metadata after 4.5 seconds of user inactivity and instantly restoring it on any mouse/touch interaction allows seamless switching between informative browsing and immersive video watching.
- Analogy: The lights in a modern smart showroom that gently dim when everyone is seated to show the product film on the main screen, but instantly brighten the moment someone stands up or touches the table.


## Hub-and-Spoke Directory Architecture (Katalog Hub me'moriyati)
- Consolidating scattered, duplicative collections into dedicated thematic destinations while anchoring the primary catalog to a clean 6-category navigation hub eliminates cognitive clutter and offers instant access paths to core media formats.
- Analogy: A major international airport terminal with 6 clearly illuminated destination gates (Domestic, International, Express, etc.), instead of a confusing bazaar where every souvenir stand and boarding gate are mixed into one chaotic corridor.

## Second-Tier Metadata Dimming & Scroll Wake-Up
- Shifting foreground movie metadata to a semi-transparent second tier (opacity-25) after initial reading allows the background video to take primary focus without disappearing, while listening to window scroll events instantly restores 100% full opacity.
- Analogy: The transparent heads-up display (HUD) on a car windshield that gently dims into the background when driving along an open highway, but immediately brightens back up the second the driver taps the brake or adjusts speed.

## Card Video Trailer Hover & Hold Preview
- Playing debounced muted video loops directly inside media card poster aspect containers on desktop hover and mobile touch-hold accelerates content discovery without forcing page transitions.
- Analogy: Moving your ear closer to a radio dial in an electronics store to hear a 3-second sample of a music track before deciding to purchase the CD.


## Dedicated Route Specialization over Polymorphic Query Views
- Routing distinct content formats to dedicated, clean URL routes (/top100, /doramas, /anime, /cartoons) rather than overloaded query parameters creates cleaner browser histories, easier bookmarking, and faster server-side rendering caches.
- Analogy: Having separate dedicated counters in a bank for Currency Exchange, Loans, and Business Accounts rather than one general queue where the teller has to change signs for every customer.

## Iframe Over-Scanning & Zero-Gap Fluid Backdrop
- Oversizing an iframe container by 140%-300% relative to a card or hero wrapper pushes native platform chrome (YouTube titles, channel avatars, and pause overlays) beyond the overflow clip boundary, producing a clean native video look.
- Analogy: Framing a panoramic art photograph with a custom pass-partout mat board that covers the photographer's metadata stamp and outer watermark on the paper edges.


## Contextual Facet Visibility (Filtr holatiga ko'ra moslashuvchan ko'rinish)
- Suppressing static category navigation tiles when active faceted search filters are engaged allows search results to rise directly below the filter controls, eliminating scrolling friction.
- Analogy: A supermarket aisle sign board that is clearly visible when entering the floor, but as soon as you open a specific product shelf, your focus is entirely on the products without the overhead signs blocking your view.
