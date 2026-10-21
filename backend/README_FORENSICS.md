# Image forensics prototypes (FYP-1 Mid)

Two prototypes that help an investigator check screenshot evidence, alongside the SHA-256 hash
from the core module:

| Question                                       | Tool   |
|------------------------------------------------|--------|
| Are these the exact same bytes?                | SHA-256|
| Do these two images look the same?             | pHash  |
| Which part of this JPEG may have been edited?  | ELA    |

**None of these prove that an image was or was not manipulated.** They point a person at what to check.

## pHash — perceptual hash

Finds the same picture again after it was resized, recompressed or forwarded, even though its SHA-256 changed.
The image is reduced to its overall structure and turned into a 256-bit hash; two images are compared by
how many bits differ: "≤ 10%" near duplicate, "≤ 25%" possibly related, otherwise different.
Results match the `imagehash` library bit-for-bit.

## ELA — error level analysis

A JPEG loses a little detail each time it is saved. ELA re-saves the image once more and shows how much
each area changed; an area pasted in later usually changes more and shows up brighter.
Output: original | ELA | heatmap (yellow = more change), plus summary numbers.

## Run (from the `backend` folder)

```
py -m pip install -r requirements.txt
py -m pytest -q
py scripts\phash_demo.py
py scripts\ela_demo.py
py -m uvicorn app.main:app --reload
```

The demos use the synthetic sample images in `forensics_samples/` and write their reports to
`forensics_results/`. For a live demo open http://127.0.0.1:8000/docs → forensics (prototype)
(`phash/compare`, `ela/image`) and set `consent` to `true`.

## Key results (synthetic samples)

- Resized / recompressed copy: SHA-256 differs, pHash only 0.8% different → recognised as the same picture.
- One chat message edited: pHash only 6.2% different → pHash cannot see small edits
- ELA on the edited JPEG: the edited message is 4.08× brighter than the other messages (2.05× without the edit).

## Limitations

- Prototype thresholds, tuned only on synthetic samples.
- Large crops, rotation and strong brightness changes move the pHash a lot.
- Text, sharp edges and coloured areas always glow in ELA; judge a bright area against similar content.
- ELA needs JPEG images; PNG screenshots have no compression history.
- Repeated recompression (e.g. forwarding) can erase ELA traces.
- Full integration into the evidence pipeline is planned for Final-1.
