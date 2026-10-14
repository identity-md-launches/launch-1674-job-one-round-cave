# Code Constants

Find address-width literals in an Ethereum contract's proof-backed historical runtime, with their byte offsets and nearby instructions. This lets a worker locate embedded values worth investigating without mistaking the many address masks in real code for external contracts. Python 3.10+; standard library only; no installation.

One command from the repository root demonstrates it offline on **real ZTO first, then IMD evidence**:

```sh
python3 -B line-3/tools/code-constants/demo.py
```

Expected: `demonstration_passed: true`. Both raw historical bundles are reverified, including account/header commitments and measured proxy slots. Saved input is in `../code-delta/zto-later-proof.json` and `imd-later-proof.json`; no network is needed. Keep the committed sibling Code Surface, Code Opcodes, Code Ancestry, Code Proof and Code Lens folders (including its Keccak implementation). No new runtime dependencies were installed.

## What happened when tried

At saved Ethereum block **26,187,032**, ZTO's 1,287-byte runtime contained no supported address-width literals. IMD's 22,990-byte runtime contained **82 mask occurrences**, **five small-integer occurrences**, and **eight address-shaped occurrences**. There are three unique IMD literals in total. All eight address-shaped occurrences encode `0x1a44076050125825900e736c501f859c50fe728c`. This is an observed constant, not a verified external contract or dependency. The small integer is 1,000,000,000,000; classifying that separately avoids treating it as a meaningful address. The saved complete demonstration is `demo-result.json`.

These raw proofs came from an earlier contributor's real read-only collection and remain **unanchored RPC headers**. This round replayed them offline; it did not collect a fresh chain observation. State inclusion is verified relative to the supplied header, whose authenticity is not established. Neither the literal inventory nor a matching checkpoint grants code approval. No funds, deployment, key, wallet, environment variables, signing, payment, posting or transaction sending is involved.

## Inspect another proof bundle

```sh
python3 -B line-3/tools/code-constants/code_constants.py --bundle line-3/tools/code-delta/imd-later-proof.json
```

The optional `--anchor-hash` accepts an independently trusted Ethereum execution block hash. Copying the hash out of the same bundle checks equality only; it supplies no independent trust. Invalid proofs and wrong hashes fail before printing any JSON. Exit 0 means the bounded inventory completed, not that the contract is safe; invalid/unavailable input exits 1, CLI syntax errors exit 2. Files must resolve inside the current workspace, be at most 100,000 bytes and have no duplicate JSON keys. The CLI writes only stdout and stderr and makes no network requests.

## Read findings carefully

The linear decoder reads the **complete runtime**, skips PUSH operand bytes, and considers complete `PUSH20` or `PUSH32` operands whose upper twelve bytes are zero. Other encodings are outside coverage. Zero, the all-ones 160-bit mask, and values below 2^64 are separate categories; all remaining supported values are called `address-shaped`. These categories describe bits, not intent. Genuine low-valued addresses can be classified as small integers; zero/masks are bytecode data, never proposed recipient addresses.

Each unique literal has an exact occurrence count, at most 32 occurrence previews, and an explicit omitted count. At most 32 unique literals are previewed per runtime; category counts and the unique count still cover all supported literals. Each preview includes at most four following decoded instructions. The `followed_by_address_eq` flag means exactly that `ADDRESS` then `EQ` immediately follow the PUSH. This can resemble a library guard, but the tool does not evaluate the stack, reachability or branch behavior and does not identify a library. A following call opcode does not prove that the literal is its target.

Recognized Solidity metadata is annotated, never excluded as presumed non-executable data. Candidate-path and beacon runtime addresses are deduplicated with roles retained; inherited warnings about unproven beacon `implementation()` results remain in the proof output. Nothing here proves external account identity, dependencies, source equivalence, custom routing, current code, consensus, finality or semantic safety. Dynamically computed and storage-loaded addresses are not inventoried.

## Checks

```sh
python3 -B -m unittest discover -s line-3/tools/code-constants -p 'test_*.py' -v
```

All 16 checks passed: real ZTO/IMD replay, mask/integer distinctions, padded operands, operand boundaries, every truncated relevant PUSH length, unreachable patterns, metadata, bounded previews, maximum runtime, corrupted proofs and consistent bytecode forgeries, anchor mismatch, beacon deduplication/warnings, input constraints and CLI failure without partial JSON. Synthetic bytecode appears only in tests, never in a delivered chain observation.

The mark's meaning: **Pepe finds a hidden pebble inside the code stone.**
