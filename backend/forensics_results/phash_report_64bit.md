# pHash prototype results (64-bit)

Generated 2026-10-20T21:28:05. Reference image: `original.png` (pHash `d62b542b542f552d`).
Verdict rule: near_duplicate if ≤ 10% of bits differ, possibly_related if ≤ 25%, otherwise different.

| Image | SHA-256 same? | Bits differ | Similarity | pHash verdict |
|---|---|---|---|---|
| brightened.png | no | 10 / 64 (15.6%) | 84.4% | possibly_related |
| cropped_top.png | no | 10 / 64 (15.6%) | 84.4% | possibly_related |
| different_screenshot.png | no | 8 / 64 (12.5%) | 87.5% | possibly_related |
| edited_one_message.png | no | 0 / 64 (0.0%) | 100.0% | near_duplicate |
| recompressed_q60.jpg | no | 0 / 64 (0.0%) | 100.0% | near_duplicate |
| resized_50.png | no | 0 / 64 (0.0%) | 100.0% | near_duplicate |
| unrelated_image.png | no | 30 / 64 (46.9%) | 53.1% | different |

## How to read this

- SHA-256 differs for every variant: any re-save or edit changes the bytes. That is the integrity check.
- pHash stays close for copies that look the same (resized, recompressed). That is how the system can
  recognise the same screenshot uploaded twice or forwarded through another app.
- pHash is a similarity measure, not proof of manipulation. A small local edit (one changed message) can
  stay close to the original; different chats in the same app can look partly similar because of the layout.
