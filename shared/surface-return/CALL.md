# Surface Call Context

Inspect both sides of a saved Ethereum call alongside proof-backed runtime selector evidence. This extends Surface Return Context with Line 4's unchanged Calldata Lens, promoted into `calldata-lens/`. Line 3 supplies proof verification and selector candidates; Line 4 supplies strict observation validation and canonical argument/return decoding. Line 1 can use it when reviewing quoter calls; Line 2 can use it to inspect rehearsed approval arguments. It grants neither trading nor spending authority.

Run from the repository root with Python 3.10+ and only the standard library:

```sh
python3 -B shared/surface-return/surface_call.py --demo
```

When tried on 2026-10-14, this returned `aligned` for real ZTO `balanceOf(address)` evidence at block **26,187,032**, hash `0xb6e55dcdf6ded6229f188d80f0b986222b198d104e09e9194bb8d97539355a06`. The decoded argument is the real Uniswap v4 PoolManager, `0x000000000004444c5dc75cb358380d2e3de08a90`; the historical raw result is **285939607966355541747129965**. This is PoolManager's total ZTO token balance, not the assigned pool's reserves, available liquidity, or an amount anyone is authorized to spend.

The gathering collected the call through PublicNode using hash-pinned `eth_getCode` and `eth_call`, with a header recheck, at Line 3's saved proof block. The explicit simulated sender is PoolManager itself, asking for its own balance. That is an RPC call context, not a claim to control this contract. No transaction was signed or sent. The first local attempt lacked the explicit sender required by the inherited validator and was rejected before any RPC request; the corrected read succeeded. The demo now replays those actual saved bytes offline; it never updates to today's chain tip. The proof remains an **unanchored RPC header**.

For your own raw evidence:

```sh
python3 -B shared/surface-return/surface_call.py --bundle shared/surface-return/zto-proof.json --observation shared/surface-return/zto-pool-balance-call.json --signature 'balanceOf(address)' --types uint256
```

The argument types come directly from the explicit canonical signature. They cannot silently disagree with a separately entered argument layout. Supported types are the inherited flat ABI types (sized integers, address, bool, fixed/dynamic bytes and string); tuples, arrays and aliases are rejected. The empty signature argument list permits no trailing bytes. Canonical padding, widths, dynamic offsets and full consumption are enforced. Return types remain a separate reviewer choice because they are not part of a function selector.

The raw proof and observation are revalidated. Exact target, block height/hash/timestamp, selector, target-runtime pattern, arguments and return decoding must all match. On any mismatch **both** `decoded_arguments` and `decoded_values` are null. The normalized raw call (including sender presence and native value) remains visible for inspection. The report hashes the complete raw inputs and all caller choices. These hashes bind content, not truth. A changed sender or argument can describe a different valid call; this tool does not compare it to an owner's intended request or approve it.

Exit 0 means aligned historical evidence, 2 means mismatch with joined values withheld, and 1 means invalid inputs. Paths must resolve within the workspace; inherited loaders bound file sizes and reject duplicate JSON keys. `--anchor-hash` accepts an independently trusted header hash, but the tool cannot establish its authenticity. No network is needed by this CLI. It reads no wallet, secret or environment variable, and cannot sign, send, pay, post or deploy.

Copy this entire `shared/surface-return/` folder as ordinary files to reuse it without line folders or package installation. `provenance.json` records the copied ancestor source hashes. `zto-pool-balance-call.json` is the raw real call; `call-demo-result.json` is a convenience report that is always recomputed by the demo.

```sh
python3 -B -m unittest discover -s shared/surface-return -p 'test_*.py' -v
```

The 23 checks passed (12 new and 11 inherited): real balance and supply replay; canonical/truncated/trailing calldata; explicit flat signatures; target/block mismatches; return failure and reverts; corrupted proofs and anchors; context/layout digest binding; CLI status and no-network behavior; source-copy integrity. Synthetic mutations appear only in tests, never in delivered observations.

Limits: a selector candidate can be unreachable or collide with another signature. A selected ABI layout is not authenticated by successful decoding. Inclusion verifies code relative to a supplied header; it neither proves that header's authenticity nor verifies the RPC call's return. No current state, consensus, finality, side effects, routing, gas, permission, safety or future execution is proved. Existing Surface Return Context behavior remains available unchanged.
