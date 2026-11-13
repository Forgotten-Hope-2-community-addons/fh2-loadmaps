# Forgotten Hope 2 Loadmaps Collector

## Description

Collects the loading-screen image of every level in a Forgotten Hope 2 mod into a single folder, named after the level folder (the same name the game uses for the map).

```
<fh2>/levels/anctoville_1944/info/loadmap.png            ->  loadmaps/anctoville_1944.png
<fh2>/levels/the_battle_for_sfakia/info/favoritemap.png  ->  loadmaps/the_battle_for_sfakia.png
```

Requires Python 3.9+. No extra packages.

## Usage

```cmd
python3 copy_loadmaps.py <fh2-mod-folder> [--overrides FILE] [--no-favoritemap]
python3 copy_loadmaps.py --help
```

> If `python` points to Python 2 on your machine (e.g. via pyenv), use `python3`.

### Choosing the FH2 folder

Pass either the mod folder or its `levels` folder. Both of these work the same:

```cmd
python3 copy_loadmaps.py "C:\Program Files (x86)\Forgotten Hope 2 Editor\mods\fh2"
python3 copy_loadmaps.py "C:\Program Files (x86)\Forgotten Hope 2 Editor\mods\fh2\levels"
```

Every subfolder of `levels` is treated as a level.

### Output folder

Images are written to `loadmaps` in the **current folder** (where you run the command, not where the script lives).

- Created if it does not exist.
- **Emptied at the start of every run**, so it only ever contains the latest results. Don't keep anything else in it.

```cmd
cd C:\temp
python3 C:\tools\fh2-loadmaps\copy_loadmaps.py "C:\...\mods\fh2"
rem -> images in C:\temp\loadmaps\
```

### Source image: favoritemap vs loadmap

Some levels have both `info/favoritemap.png` and `info/loadmap.png`.

| Command | Level has favoritemap | Level has only loadmap |
|---|---|---|
| default | `favoritemap.png` | `loadmap.png` |
| `--no-favoritemap` | `loadmap.png` | `loadmap.png` |

```cmd
python3 copy_loadmaps.py "C:\...\mods\fh2" --no-favoritemap
```

Levels with neither image are skipped and listed as `Skipped`.

### Output file names

The name of each image is:

1. The **override** from the overrides file, if there is one (used exactly as written).
2. Otherwise the **level folder name**, normalized.

| Folder | Output |
|---|---|
| `battle_of_brest` | `battle_of_brest.png` |
| `anctoville_1944` | `anctoville_1944.png` |
| `tunis_1943` | `tunis_1943.png` |

#### Normalization

- Leading/trailing spaces are trimmed.
- Lowercased.
- Any run of whitespace becomes a single `_`.
- Everything else is **kept**, including hyphens and accents.

Discord Art Assets sanitize special characters out of asset keys on upload. If a folder name has characters other than `a-z`, `0-9` and `_`, add an override so the file name matches the key the game sends.

### Name overrides

By default the script reads `loadmap_overrides.json` next to the script. It maps **level folder name** to **output name**:

```json
{
  "crete_1941": "crete",
  "tunis_1943": "tunis"
}
```

- Keys are level folder names (case-insensitive).
- Values are used **as-is**, no normalization. `"Crete"` gives `Crete.png`.
- A trailing `.png` in the value is optional.
- An override for a folder that doesn't exist prints a `Warning`.
- If the file doesn't exist, no overrides are used.

Use a different file:

```cmd
python3 copy_loadmaps.py "C:\...\mods\fh2" --overrides my_overrides.json
```

### Name conflicts

If two levels end up with the same output name (case-insensitive), the first one (alphabetically by folder) is copied and the second is reported. For example, with the override `"crete_1941": "the_battle_for_sfakia"`:

```
CONFLICT the_battle_for_sfakia -> the_battle_for_sfakia.png already used by crete_1941; add an override for one of them
```

Fix it with an override. The script exits with code `1` when there are conflicts, `0` otherwise.

### Example output

```
Copied   anctoville_1944/info/loadmap.png -> anctoville_1944.png (folder name)
Copied   bardia/info/favoritemap.png -> bardia.png (folder name)
Copied   crete_1941/info/favoritemap.png -> crete.png (override)
Skipped  bjerkvik (no info/favoritemap.png or info/loadmap.png)

Done: 106 copied, 18 skipped, 0 conflicts. Output: C:\temp\loadmaps
```
