# Gathering 10

This gathering tested all four lines and added [Surface Call Context](../shared/surface-return/CALL.md): proof-backed selector evidence joined with canonical calldata arguments and return values. Its real ZTO PoolManager-balance demonstration works offline with Python's standard library:

```sh
python3 -B shared/surface-return/surface_call.py --demo
```

The command prints `aligned` at historical block 26,187,032. It describes an explicit read-only simulation context, not permission to transact. The whole shared folder contains ordinary source and real evidence files; no dependency installation or network is needed.

[REPORT.md](REPORT.md) records each line's trials, what works, what is broken and goal scope. [COINS.md](COINS.md) says none: ZTO and IMD meet the asset needs. [VISUAL.md](VISUAL.md) records image dimensions, formats and preservation review. [The gallery](../dist/index.html) contains every numbered record by wall, newest painted first, with future placeholders below.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery.py
```

The check run passed 99 expected outcomes and 619 tests. `run_suite.py` confines test temporary directories to `test/scratch/`; line files remain unchanged. The delivery checker validates image bytes, records, gallery, size bounds and changed paths. Results are local contributor evidence, not independent certification.

`try_surface_call.py` documents the optional read-only historical RPC collection, with a 45-second process deadline per provider. It refuses to overwrite the delivered raw observation, so use the offline demo to reproduce this deliverable. No wallet, key, secret, environment variable, signing, sending, payment or deployment is used.
