# Meshy Prompts — "Sugar Rush" theme

Each block below is a **complete prompt**, tail already appended. Copy, paste
into Meshy **Text to 3D**, generate. As of: 2026-09-11.

**In Meshy:** Meshy-6, symmetry on for anything round. If a result drifts,
take the best one as a reference image and continue with **Image to 3D**.
Export as multi-color 3MF, color count = however many filaments are actually
loaded.

**Meshy doesn't make the marker.** Meshy's color quantization would blur the
cell edges. It gets added in Bambu Studio: `markers/aruco_marker_<id>.svg`
(or later the STL, see `docs/todo.md`) as a **modifier with dark filament**,
sunk a bit into the surface from above.

The name after each title is the sprite in `game/themes/sugar_rush.py`. Once
an object is printed, its marker ID belongs there in `SPRITE`.

---

## Why the tails look like this

Three tails, depending on the top. Each enforces the same things:

- **Nothing on top in the middle.** A cherry, candle, or figure would sit
  right on the marker. Decoration only at the edge and sides.
- **Top surface light and smooth.** No swirl ridges, no loose sprinkles.
- **At most ~5 mm of height difference above the marker face.** Simulated:
  up to a ~10° cone works anywhere on the tray, 20–30° only in the middle of
  the tray.
- **Flat bottom, single piece, no plate.** Printable, stable, and Meshy
  otherwise likes to attach a plate or a fork.
- **Top surface at least ~45 mm wide** after scaling (30 mm marker plus
  light border). Measure the SO-101's gripper width beforehand: grabbing
  happens at the cup or the side, not the top.

---

## Colors: Bambu and CMYK

Tested (synthetically, 36 px per marker, noise and side lighting) with the
hex values from the Bambu PLA Matte table:

| Marker face (light) | Cells (dark) | Detection |
|---|---|---|
| Ivory White, Desert Tan, Latte Brown, Sakura Pink, Lemon Yellow, Ice Blue, Apple Green | Charcoal, Dark Chocolate, Plum, Dark Blue | **98–100%** |
| Bone White, Mandarin Orange, Lilac Purple | same | 85–100%, risky |
| Caramel, Scarlet Red | — | body only, never the marker |
| — | Dark Brown | too light as a cell color |

**Inverted** (light cells on a dark background, for chocolate cake): Ivory on
Dark Chocolate 100%, Desert Tan 98%, Lemon 90%, Sakura only 85%. So Ivory or
Desert Tan. The detector recognizes both directions (`detectInvertedMarker`).

**CMYK color mixing (Bambu Studio ≥ 2.5.3) — what it can and can't do:**

- It mixes by splitting a layer into thinner sub-layers of different
  filaments. Bambu recommends this **only for near-vertical walls**,
  explicitly not for slopes and top surfaces. The marker face is exactly
  that. **So topping and marker always from a single, unmixed filament.**
- Allowed to be mixed: cup wall, cake sides, the layer stripes of the cake
  slices, the chocolate wrapper. There you see the color from the side.
- **Cyan and magenta don't work as a marker face** (too dark in grayscale,
  magenta came out at 0% in testing). Yellow and white do.
- The CMYW set has **no black**. Load Charcoal (Matte) in addition for the
  marker cells.
- The CMYW set is PLA Basic, so it's glossy. Prefer Matte on the marker
  face — gloss reflects the hall lighting as a white spot.

**H2C with Vortek:** 7 hotends (1 fixed, 6 swappable), filament changes with
almost no purging. Suggested assignment: Charcoal and Ivory Matte fixed
(markers), cyan, magenta, yellow, white for mixing, Dark Chocolate for the
chocolate items.

- **All objects on one plate.** The color changes per layer then happen once
  for everything instead of once per object. That matters most for the cone
  cupcakes, whose marker zone spans ~25 layers.
- **Print a test tile per color pair first** (40 mm marker) and hold it up
  to the Mac webcam. The game runs on the Mac and shows detection live.

---

## Tails for reference

Already baked into every prompt below, here only for adjusting.

**Cone** (cupcakes):
```
, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

**Dome** (macarons, Berliner, muffin):
```
, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

**Flat** (cakes, cake slices, petit fours, chocolate):
```
, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Cupcakes

Ladder from cheap/light to expensive/tippy. The height comes from the cup
and tiers, the cap stays flat.

### 1 · Mini muffin — marker face Ivory (powdered sugar), cells Charcoal
```
Cartoon mini muffin, short and wide, golden muffin top dusted with white powdered sugar, low paper cup, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

### 2 · Vanilla — `cupcake_*` — Ivory, Charcoal
```
Cartoon vanilla cupcake, cream frosting, wide pastel paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 3 · Chocolate with pink frosting — `cupcake_choc` — Sakura, Dark Chocolate
```
Cartoon chocolate cupcake, chocolate sponge, pale pink frosting, brown ribbed paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 4 · Strawberry — `cupcake_pink` — Sakura, Plum
```
Cartoon strawberry cupcake, pink frosting, strawberry slices around the rim, pastel paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 5 · Lemon — `cupcake_lemon` — Lemon Yellow, Charcoal
```
Cartoon lemon cupcake, pale yellow frosting, lemon wedges on the rim edge, pink paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 6 · Mint chocolate — `cupcake_mint` — Apple Green, Dark Chocolate
```
Cartoon mint chip cupcake, mint green frosting, chocolate chips on the rim, taller purple paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 7 · Red velvet — Ivory (cream cheese), Charcoal
```
Cartoon red velvet cupcake, red sponge, white cream cheese frosting, tall narrow paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 8 · Blueberry, overhanging — Ice Blue, Dark Blue
Top-heavy: wide frosting on a narrow cup.
```
Cartoon blueberry cupcake, wide overhanging pale blue frosting on a narrow tall paper cup, blueberries around the rim, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 9 · Two tiers — Sakura, Plum
```
Cartoon two-tier cupcake, two stacked frosting layers, candy-striped narrow tall paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 10 · Luxury gold — Desert Tan, Charcoal
The most expensive piece: tall, narrow, tippy.
```
Cartoon luxury cupcake, cream frosting, gold leaf flakes on the sides, narrow tall black-and-gold paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

---

## Macarons

Low and wide: the lightest pieces, so the cheapest.

### Pink — `macaron_pink` — Sakura, Charcoal
```
Cartoon pink macaron, two smooth round shells with a white cream filling, ruffled shell feet, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

### Mint — `macaron_mint` — Ice Blue, Dark Blue
```
Cartoon pale blue macaron, two smooth round shells with a white cream filling, ruffled shell feet, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

### Lemon — `macaron_lemon` — Lemon Yellow, Charcoal
```
Cartoon yellow lemon macaron, two smooth round shells with a white cream filling, ruffled shell feet, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

---

## Petit Fours

Square top: fits the square marker best.

### Pink — `petitfour_pink` — Sakura, Plum
```
Cartoon petit four, small square cake cube covered in smooth pink fondant, tiny sugar flower on the front side, pale blue ribbon around the middle, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

### Mint — `petitfour_mint` — Ice Blue, Dark Blue
```
Cartoon petit four, small square cake cube covered in smooth pale blue fondant, tiny sugar flower on the front side, pink ribbon around the middle, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Chocolate — `bar_milk` — label Ivory, Charcoal

The marker sits on the label area. Label ≥ 45 mm after scaling.
```
Cartoon chocolate bar lying flat, partly unwrapped, chunky chocolate squares showing at one end, red paper wrapper with a large plain cream label area on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Berliner — `berliner` — powdered sugar Ivory, Charcoal

Not a donut with a hole: the hole would cut through the marker.
```
Cartoon filled doughnut without a hole, round puffy golden dough, white powdered sugar on top, strawberry jam peeking out of one side, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

---

## Cake slices

The top surface is a triangle. For a 30 mm marker with a border to fit, a
piece with a 60° tip needs **~70 mm length** (45° → ~80 mm). The wedge shape
slips out of the gripper, which is the difficulty lever.

### Strawberry — `slice_straw` — Sakura, Plum
```
Cartoon slice of strawberry layer cake, wide wedge shape with a 60 degree tip, three sponge layers with pink cream visible on the cut sides, pink frosting on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

### Chocolate — `slice_choc` — Ivory (cream on top), Dark Chocolate
```
Cartoon slice of chocolate layer cake, wide wedge shape with a 60 degree tip, dark chocolate sponge layers with white cream filling visible on the cut sides, white cream frosting on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

### Lemon — `slice_lemon` — Lemon Yellow, Charcoal
```
Cartoon slice of lemon layer cake, wide wedge shape with a 60 degree tip, sponge layers with pale yellow lemon cream visible on the cut sides, pale yellow frosting on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Chocolate cake — `cake_choc` — **inverted:** Dark Chocolate, cells Ivory

```
Cartoon round chocolate cake, dark chocolate ganache covering the top and sides, chocolate drips running down the sides, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Mini layer cake — `cake_straw` — Sakura, Plum

The tallest piece. Decoration only at the bottom edge, nothing on top.
```
Cartoon tall mini layer cake, three tiers of sponge and strawberry cream visible as stripes on the sides, smooth pink fondant top, piped cream decoration only around the bottom edge, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

Sources: [Bambu PLA Matte hex table](https://store.bblcdn.eu/s8/default/f131f643495b417197832b291fc7b068/Bambu_PLA_Matte_Hex_Code.pdf) ·
[Bambu Wiki: Vortek](https://wiki.bambulab.com/en/h2c/manual/Vortek-workflow-and-function) ·
[Color Mixing Guide (smith3d)](https://www.smith3d.com/bambu-studios-new-color-mixing-feature/) ·
[Meshy Prompt Guide](https://www.meshy.ai/tutorials/3d-prompt-guide)
