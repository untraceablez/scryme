# Supported Formats

scryme recognizes several export formats by inspecting the CSV header — detection is automatic and
unambiguous. The tables below show how each app's columns map to scryme's internal fields. Anything
it doesn't recognize falls back to the [column-mapping wizard](#anything-else-the-column-mapping-wizard).

## ManaBox

ManaBox includes a **Scryfall ID**, the most reliable match key.

**Header**

```
Binder Name,Binder Type,Name,Set code,Set name,Collector number,Foil,Rarity,Quantity,
ManaBox ID,Scryfall ID,Purchase price,Misprint,Altered,Condition,Language,
Purchase price currency,Added
```

| ManaBox column | scryme field |
| --- | --- |
| `Name` | name |
| `Set code` | set code |
| `Collector number` | collector number |
| `Scryfall ID` | scryfall id *(primary match)* |
| `Foil` | finish (`normal` / `foil` / `etched`) |
| `Quantity` | quantity |
| `Condition` | condition |
| `Language` | language |
| `Purchase price` | purchase price |
| `Binder Name` | binder |

**Detected by:** presence of both `Scryfall ID` and `ManaBox ID`.

## Dragon Shield

Dragon Shield (MTG Scanner) has **no Scryfall ID**, so rows match on set code + collector number.
The export begins with a `sep=,` line, which scryme strips automatically.

**Header**

```
sep=,
Folder Name,Quantity,Trade Quantity,Card Name,Set Code,Set Name,Card Number,Condition,
Printing,Language,Price Bought,Date Bought,LOW,MID,MARKET
```

| Dragon Shield column | scryme field |
| --- | --- |
| `Card Name` | name |
| `Set Code` | set code *(primary match, with Card Number)* |
| `Card Number` | collector number |
| `Printing` | finish (`Normal` / `Foil` / `Etched`) |
| `Quantity` | quantity |
| `Condition` | condition |
| `Language` | language (`English` → `en`, etc.) |
| `Price Bought` | purchase price |
| `Folder Name` | binder |

**Detected by:** presence of `Trade Quantity`, `Card Name`, and `Card Number`.

## Delver Lens

Delver Lens has a configurable, Deckbox-compatible export. scryme reads its columns
case-insensitively and accepts several aliases. When a **Scryfall ID** is present it is used as the
primary match key.

| Delver / Deckbox column | scryme field |
| --- | --- |
| `Name` / `Card Name` | name |
| `Set Code` / `Set` | set code |
| `Card Number` / `Collector Number` / `Number` | collector number |
| `Scryfall ID` | scryfall id *(primary match when present)* |
| `Foil` / `Printing` / `Finish` | finish |
| `Quantity` / `Count` | quantity |
| `Condition` | condition |
| `Language` / `Lang` | language |
| `My Price` / `Purchase Price` / `Price` | purchase price |

**Detected by:** a `Scryfall ID` column, or `Edition` + `Card Number` (and never a ManaBox file).

## Moxfield

Moxfield's collection CSV has **no Scryfall ID**, so rows match on set code (`Edition`) + collector
number.

**Header**

```
Count,Tradelist Count,Name,Edition,Condition,Language,Foil,Tags,Last Modified,
Collector Number,Alter,Proxy,Purchase Price
```

| Moxfield column | scryme field |
| --- | --- |
| `Name` | name |
| `Edition` | set code *(primary match, with Collector Number)* |
| `Collector Number` | collector number |
| `Foil` | finish (`foil` / `etched` / empty) |
| `Count` | quantity |
| `Condition` / `Language` / `Purchase Price` | condition / language / purchase price |

**Detected by:** `Tradelist Count` + `Edition` + `Collector Number` + `Purchase Price`.

## Archidekt

Archidekt's collection CSV carries a **Scryfall ID** (primary match) and an explicit `Finish`.

**Header**

```
Quantity,Name,Finish,Condition,Date Added,Language,Purchase Price,Tags,Edition Name,
Edition Code,Multiverse Id,Scryfall ID,MTGO ID,Collector Number
```

| Archidekt column | scryme field |
| --- | --- |
| `Name` | name |
| `Scryfall ID` | scryfall id *(primary match)* |
| `Edition Code` | set code |
| `Collector Number` | collector number |
| `Finish` | finish (`Normal` / `Foil` / `Etched`) |
| `Quantity` / `Condition` / `Language` / `Purchase Price` | quantity / condition / language / purchase price |

**Detected by:** `Edition Code` + `Scryfall ID`.

## Anything else: the column-mapping wizard

If your file is a CSV that scryme doesn't recognize — a TCGplayer or Deckbox export, a spreadsheet
you made yourself, anything — uploading it opens a **mapping wizard** instead of an error. It reads
the file's column headers and lets you match each one to a scryme field (card name, quantity, set
code, collector number, Scryfall ID, finish, condition, language, purchase price). scryme guesses
the obvious ones; you confirm or adjust, and only **Card name** is required. From there it's the
same preview → confirm flow as a recognized format.

## Adding a new format

Importers self-register. To add one, create a module in `backend/src/importers/` with a class that
implements `detect(text)` and `parse(text)` (returning `ImportRow`s) and is decorated with
`@register`, then import it in `backend/src/importers/__init__.py`. Detection rules should be
specific enough not to overlap with existing formats.
