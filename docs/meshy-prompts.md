# Meshy-Prompts — Thema „Sugar Rush"

Jeder Block unten ist ein **kompletter Prompt**, Tail schon angehängt. Kopieren,
in Meshy **Text to 3D** einfügen, generieren. Stand: 11. September 2026.

**In Meshy:** Meshy-6, Symmetrie an bei allem Runden. Driftet ein Ergebnis, das
beste als Referenzbild nehmen und mit **Image to 3D** weitermachen. Export als
Multi-Color-3MF, Farbanzahl = so viele Filamente, wie wirklich geladen sind.

**Den Marker macht nicht Meshy.** Meshys Farbquantisierung würde die Zellkanten
verwischen. Er kommt in Bambu Studio dazu: `markers/aruco_marker_<id>.svg` (oder
später die STL, siehe `docs/todo.md`) als **Modifier mit dunklem Filament**, von
oben ein Stück in die Oberfläche.

Der Name hinter jedem Titel ist das Sprite in `game/themes/sugar_rush.py`. Wird
ein Objekt gedruckt, gehört seine Marker-ID dort in `SPRITE`.

---

## Warum die Tails so aussehen

Drei Tails, je nach Oberseite. Jeder erzwingt dasselbe:

- **Nichts oben in der Mitte.** Eine Kirsche, Kerze oder Figur säße genau auf
  dem Marker. Deko nur an Rand und Seiten.
- **Oberseite hell und glatt.** Keine Wirbelrippen, keine losen Streusel.
- **Höchstens ~5 mm Höhenunterschied über der Markerfläche.** Simuliert: bis
  ~10° Kegel geht überall auf dem Tablett, 20–30° nur in der Tablettmitte.
- **Flacher Boden, ein Stück, keine Teller.** Druckbar, standfest, und Meshy
  hängt sonst gern einen Teller oder eine Gabel an.
- **Oberseite mindestens ~45 mm breit** nach dem Skalieren (30-mm-Marker plus
  heller Rand). Die Greiferbreite des SO-101 vorher messen: gegriffen wird am
  Becher oder an der Seite, nicht oben.

---

## Farben: Bambu und CMYK

Getestet (synthetisch, 36 px pro Marker, Rauschen und Seitenlicht) mit den
Hex-Werten der Bambu-PLA-Matte-Tabelle:

| Markerfläche (hell) | Zellen (dunkel) | Erkennung |
|---|---|---|
| Ivory White, Desert Tan, Latte Brown, Sakura Pink, Lemon Yellow, Ice Blue, Apple Green | Charcoal, Dark Chocolate, Plum, Dark Blue | **98–100 %** |
| Bone White, Mandarin Orange, Lilac Purple | dieselben | 85–100 %, riskant |
| Caramel, Scarlet Red | — | nur Körper, nie Marker |
| — | Dark Brown | zu hell als Zellfarbe |

**Invertiert** (helle Zellen auf dunklem Grund, für Schokokuchen): Ivory auf
Dark Chocolate 100 %, Desert Tan 98 %, Lemon 90 %, Sakura nur 85 %. Also Ivory
oder Desert Tan. Der Detektor erkennt beide Richtungen (`detectInvertedMarker`).

**CMYK-Farbmischung (Bambu Studio ≥ 2.5.3) — was sie darf und was nicht:**

- Sie mischt, indem sie eine Schicht in dünnere Teilschichten verschiedener
  Filamente zerlegt. Bambu empfiehlt das **nur für fast senkrechte Wände**,
  ausdrücklich nicht für Schrägen und Oberseiten. Die Markerfläche ist genau
  das. **Topping und Marker also immer aus einem einzigen, ungemischten
  Filament.**
- Gemischt werden darf: Becherwand, Tortenseiten, Schichtstreifen der
  Kuchenstücke, Wrapper der Schokolade. Dort sieht man die Farbe von der Seite.
- **Cyan und Magenta taugen nicht als Markerfläche** (zu dunkel im Grauwert,
  Magenta lag im Test bei 0 %). Gelb und Weiß schon.
- Das CMYW-Set hat **kein Schwarz**. Für die Markerzellen deshalb Charcoal
  (Matte) zusätzlich laden.
- Das CMYW-Set ist PLA Basic, also glänzend. Auf der Markerfläche lieber
  Matte, Glanz spiegelt die Hallenbeleuchtung als weißen Fleck.

**H2C mit Vortek:** 7 Hotends (1 fest, 6 wechselbar), Filamentwechsel fast
ohne Spülen. Vorschlag für die Belegung: Charcoal und Ivory Matte fest
(Marker), Cyan, Magenta, Gelb, Weiß für die Mischung, Dark Chocolate für die
Schokosachen.

- **Alle Objekte auf eine Platte.** Die Farbwechsel pro Schicht fallen dann
  einmal für alle an statt einmal pro Objekt. Das zählt vor allem bei den
  Kegel-Cupcakes, deren Markerzone über ~25 Schichten läuft.
- **Vorher ein Testplättchen pro Farbpaar drucken** (40 mm Marker) und vor die
  Mac-Webcam halten. Das Spiel läuft am Mac und zeigt die Erkennung live.

---

## Tails zum Nachschlagen

Stecken unten schon in jedem Prompt, hier nur zum Anpassen.

**Kegel** (Cupcakes):
```
, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

**Kuppel** (Macarons, Berliner, Muffin):
```
, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

**Flach** (Kuchen, Kuchenstücke, Petit Fours, Schokolade):
```
, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Cupcakes

Leiter von billig/leicht nach teuer/kippelig. Die Höhe kommt aus Becher und
Etagen, die Kappe bleibt flach.

### 1 · Mini-Muffin — Markerfläche Ivory (Puderzucker), Zellen Charcoal
```
Cartoon mini muffin, short and wide, golden muffin top dusted with white powdered sugar, low paper cup, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

### 2 · Vanille — `cupcake_*` — Ivory, Charcoal
```
Cartoon vanilla cupcake, cream frosting, wide pastel paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 3 · Schoko mit rosa Frosting — `cupcake_choc` — Sakura, Dark Chocolate
```
Cartoon chocolate cupcake, chocolate sponge, pale pink frosting, brown ribbed paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 4 · Erdbeer — `cupcake_pink` — Sakura, Plum
```
Cartoon strawberry cupcake, pink frosting, strawberry slices around the rim, pastel paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 5 · Zitrone — `cupcake_lemon` — Lemon Yellow, Charcoal
```
Cartoon lemon cupcake, pale yellow frosting, lemon wedges on the rim edge, pink paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 6 · Minze-Schoko — `cupcake_mint` — Apple Green, Dark Chocolate
```
Cartoon mint chip cupcake, mint green frosting, chocolate chips on the rim, taller purple paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 7 · Red Velvet — Ivory (Frischkäse), Charcoal
```
Cartoon red velvet cupcake, red sponge, white cream cheese frosting, tall narrow paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 8 · Blaubeere, überhängend — Ice Blue, Dark Blue
Kopflastig: breites Frosting auf schmalem Becher.
```
Cartoon blueberry cupcake, wide overhanging pale blue frosting on a narrow tall paper cup, blueberries around the rim, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 9 · Zwei Etagen — Sakura, Plum
```
Cartoon two-tier cupcake, two stacked frosting layers, candy-striped narrow tall paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

### 10 · Luxus-Gold — Desert Tan, Charcoal
Das teuerste Stück: hoch, schmal, kippelig.
```
Cartoon luxury cupcake, cream frosting, gold leaf flakes on the sides, narrow tall black-and-gold paper cup, smooth low cone-shaped frosting cap with a gentle slope, clean uninterrupted top surface, pastel frosting, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no cherry or toppings on top, no plate, no loose sprinkles
```

---

## Macarons

Niedrig und breit: die leichtesten Stücke, also die billigsten.

### Rosa — `macaron_pink` — Sakura, Charcoal
```
Cartoon pink macaron, two smooth round shells with a white cream filling, ruffled shell feet, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

### Minze — `macaron_mint` — Ice Blue, Dark Blue
```
Cartoon pale blue macaron, two smooth round shells with a white cream filling, ruffled shell feet, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

### Zitrone — `macaron_lemon` — Lemon Yellow, Charcoal
```
Cartoon yellow lemon macaron, two smooth round shells with a white cream filling, ruffled shell feet, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

---

## Petit Fours

Quadratische Oberseite: passt am besten zum quadratischen Marker.

### Rosa — `petitfour_pink` — Sakura, Plum
```
Cartoon petit four, small square cake cube covered in smooth pink fondant, tiny sugar flower on the front side, pale blue ribbon around the middle, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

### Minze — `petitfour_mint` — Ice Blue, Dark Blue
```
Cartoon petit four, small square cake cube covered in smooth pale blue fondant, tiny sugar flower on the front side, pink ribbon around the middle, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Schokolade — `bar_milk` — Label Ivory, Charcoal

Der Marker sitzt auf der Etikettfläche. Etikett nach dem Skalieren ≥ 45 mm.
```
Cartoon chocolate bar lying flat, partly unwrapped, chunky chocolate squares showing at one end, red paper wrapper with a large plain cream label area on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Berliner — `berliner` — Puderzucker Ivory, Charcoal

Kein Donut mit Loch: das Loch schneidet den Marker.
```
Cartoon filled doughnut without a hole, round puffy golden dough, white powdered sugar on top, strawberry jam peeking out of one side, smooth low dome top with a gentle slope, clean uninterrupted top surface, flat bottom, chunky simple shapes, matte, symmetrical, single solid piece, no plate, no text, no loose sprinkles
```

---

## Kuchenstücke

Die Oberseite ist ein Dreieck. Damit ein 30-mm-Marker mit Rand hineinpasst,
braucht ein Stück mit 60°-Spitze **~70 mm Länge** (45° → ~80 mm). Die
Keilform rutscht aus dem Greifer, das ist der Schwierigkeitshebel.

### Erdbeer — `slice_straw` — Sakura, Plum
```
Cartoon slice of strawberry layer cake, wide wedge shape with a 60 degree tip, three sponge layers with pink cream visible on the cut sides, pink frosting on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

### Schoko — `slice_choc` — Ivory (Sahne oben), Dark Chocolate
```
Cartoon slice of chocolate layer cake, wide wedge shape with a 60 degree tip, dark chocolate sponge layers with white cream filling visible on the cut sides, white cream frosting on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

### Zitrone — `slice_lemon` — Lemon Yellow, Charcoal
```
Cartoon slice of lemon layer cake, wide wedge shape with a 60 degree tip, sponge layers with pale yellow lemon cream visible on the cut sides, pale yellow frosting on top, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Schokokuchen — `cake_choc` — **invertiert:** Dark Chocolate, Zellen Ivory

```
Cartoon round chocolate cake, dark chocolate ganache covering the top and sides, chocolate drips running down the sides, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

## Mini-Schichttorte — `cake_straw` — Sakura, Plum

Das höchste Stück. Deko nur unten am Rand, nichts oben.
```
Cartoon tall mini layer cake, three tiers of sponge and strawberry cream visible as stripes on the sides, smooth pink fondant top, piped cream decoration only around the bottom edge, flat smooth top surface with nothing on it, flat bottom, chunky simple shapes, matte, single solid piece, no plate, no fork, no text, no loose crumbs or sprinkles
```

---

Quellen: [Bambu PLA Matte Hex-Tabelle](https://store.bblcdn.eu/s8/default/f131f643495b417197832b291fc7b068/Bambu_PLA_Matte_Hex_Code.pdf) ·
[Bambu Wiki: Vortek](https://wiki.bambulab.com/en/h2c/manual/Vortek-workflow-and-function) ·
[Color Mixing Guide (smith3d)](https://www.smith3d.com/bambu-studios-new-color-mixing-feature/) ·
[Meshy Prompt Guide](https://www.meshy.ai/tutorials/3d-prompt-guide)
