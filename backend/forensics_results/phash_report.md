# pHash prototype results (256-bit)

Generated 2026-10-20T21:27:38. Reference image: `original.png` (pHash `d6a8295554aa2b5454aa2d5454aa295564aa2a55d728abf5a0e797f892ffc2af`).
Verdict rule: near_duplicate if ≤ 10% of bits differ, possibly_related if ≤ 25%, otherwise different.

| Image | SHA-256 same? | Bits differ | Similarity | pHash verdict |
|---|---|---|---|---|
| brightened.png | no | 36 / 256 (14.1%) | 85.9% | possibly_related |
| cropped_top.png | no | 80 / 256 (31.2%) | 68.8% | different |
| different_screenshot.png | no | 52 / 256 (20.3%) | 79.7% | possibly_related |
| edited_one_message.png | no | 16 / 256 (6.2%) | 93.8% | near_duplicate |
| recompressed_q60.jpg | no | 2 / 256 (0.8%) | 99.2% | near_duplicate |
| resized_50.png | no | 2 / 256 (0.8%) | 99.2% | near_duplicate |
| unrelated_image.png | no | 130 / 256 (50.8%) | 49.2% | different |

## How to read this

- SHA-256 differs for every variant: any re-save or edit changes the bytes. That is the integrity check.
- pHash stays close for copies that look the same (resized, recompressed). That is how the system can
  recognise the same screenshot uploaded twice or forwarded through another app.
- pHash is a similarity measure, not proof of manipulation. A small local edit (one changed message) can
  stay close to the original; different chats in the same app can look partly similar because of the layout.
