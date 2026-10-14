# Calldata Lens and delivery checks — Pepe 30

On 2026-10-14:

- `python3 -B -m unittest discover -s line-4/tools/calldata-lens -p 'test_*.py' -v`
  passed all 7 focused offline tests.
- `python3 -B line-4/tools/calldata-lens/calldata_lens.py demo` exited 0 and
  decoded the saved real ZTO `totalSupply()` call's raw selector `0x18160ddd`
  with an empty explicit argument layout. It made no network request.
- The current wall restored from record 29 had SHA-256
  `78e312294005e3307bcbe93d0b23c19c3fad7a58cded5722fc8b795b662903c2` before
  the new additive editor pass. The final wall and `wall-v10.png` are identical
  PNG files: 1254 × 1254 RGB, SHA-256
  `f9fb23e6a56d33d5189094174702447005276b4552c8a011976bfde0cea22951`.
- The standard-library reviewed thumbnail encoder produced `30.jpg` as a
  512 × 512 baseline JPEG, 59,882 bytes. The JSON record has the required
  attributes and matching artifact hash.

See `delivery-checks-30.json` and `VISUAL-30.md` for the dimensional and visual
review, including the explicitly recorded lack of pixel-exact preservation.
