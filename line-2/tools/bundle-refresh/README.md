# Bundle Refresh

Recheck an entire reviewed unsigned ERC-20 revoke handoff before releasing it for an owner's independent review. Every previously measured pair must be rechecked at one later block. An altered or incomplete original bundle, missing or extra pair, changed or cleared candidate allowance, newly violating permission, or stale recheck withholds **the entire bundle**. No partial candidate list is released.

Python 3.10+; standard library only, using the adjacent Draft Bundle, Approval Draft, Permission Gate, Allowance Changes and Allowance Lens sources. Run from the repository root. One command demonstrates it offline:

```sh
python3 -B line-2/tools/bundle-refresh/bundle_refresh.py
```

It returns `release_bundle_for_owner_review`, `accepted: true`, 19 rechecked pairs, three reviewed candidates and an age of zero blocks. This replays saved real ZTO evidence, not the current chain tip. It prints JSON and writes no files.

## What happened when tried

On 2026-10-14, used read-only Ethereum RPC through this assignment's contributor route, publicly attributed to [Ethereum PublicNode](https://ethereum-rpc.publicnode.com). Rechecked all 19 pairs from the ancestor ZTO inventory at block **26,187,572**, hash `0xfbdf6fb511bd7ee2e74dd1b2bd8982e05e2d4cf8d10e495e6b9789bc50e7997f`. Confirmed the original reviewed block's hash, used canonical block-hash-pinned `eth_call` for decimals, balances and allowances, checked consistent headers across owners and reread the final header. A separate finalized reference request returned the same block. All three reviewed allowances were unchanged, no new policy violations were observed, and the entire reviewed bundle passed. Two candidates still had empty balances; their permissions remain active.

`live-after.json` retains the complete raw rechecked inventory, `live-reference.json` the separately requested reference, and `live-review.json` the actual eight-block-limit review. The default demonstration recomputes everything with a stricter zero-block limit. Historical evidence remains historical regardless of when you replay it.

Fifteen focused tests passed, exercising original bundle omissions, duplicate substitution, altered calldata and anchors; lost and expanded inventory coverage; changed, cleared and newly violating permissions; reduction to a nonzero ceiling; balance-only changes; inclusive age boundaries; reference conflicts; insufficient initial evidence; empty candidate sets; digest binding; CLI exits; duplicate keys, byte limits and workspace-only input paths. Synthetic mutations exist only in tests and are never delivered as chain observations.

## Review a received bundle

Provide all five JSON inputs and your own inclusive block-age limit:

```sh
python3 -B line-2/tools/bundle-refresh/bundle_refresh.py --bundle path/to/bundle.json --before path/to/reviewed-inventory.json --policy path/to/policy.json --after path/to/later-inventory.json --reference path/to/reference.json --maximum-age-blocks 8
```

All paths must resolve inside the current workspace; each input is limited to 96 KiB and duplicate JSON keys are refused. Bundle format is Draft Bundle's `permission-draft-bundle-v1`; before/after evidence is raw Allowance Lens observations or Allowance Changes inventories, never precomputed acceptance reports. Policy is Permission Gate's explicit policy. Reference format is Draft Age's `permission-reference-block-v1`, with exactly `schema`, integer `chain_id: 1`, an allowed public `source`, and `block` containing canonical RPC `number`, 32-byte `hash`, and `timestamp`. At the same height, its hash and timestamp must match the recheck. The reference must never precede that recheck.

The original policy's block interval validates **initial review**. Its pair ceilings (zero for unlisted measured pairs) continue to apply to rechecked permissions. This tool does not silently extend a policy interval or create new revoke candidates. If a pair becomes violating, or an old violating allowance changes, make a new explicit review and bundle. Even a cleared candidate withholds the old whole handoff, instead of quietly dropping it.

Balances may change without withholding: permission is tested independently of current balance. Released candidates retain their original historical `balance_raw`; the new balances are supplied separately in `pair_reviews`. Do not mistake historical candidate fields for current state. Digests bind all five parsed JSON inputs using sorted compact JSON SHA-256; they do not authenticate a provider.

Exit **0**: accepted for owner review (including a sufficient review with no candidates). Exit **3**: entire bundle withheld, with reasons and `owner_review_bundle: null`. Exit **1**: malformed or inconsistent input; no bundle returned.

To capture another complete example, the optional read-only helper uses the ancestor inventory and policy, and writes three bounded JSON files to a **new** directory inside this tool folder:

```sh
python3 -B line-2/tools/bundle-refresh/capture_example.py --output line-2/tools/bundle-refresh/new-capture
```

Its default RPC is PublicNode; `--rpc https://eth.drpc.org` also works. The assignment-only loopback choice is machine-specific and is never named as a public evidence source. The helper enforces a 55-second total read deadline and saves no partial read. Saved reports may show withholding if real permissions changed; it does not manufacture a passing example. For a network-free check, use the first command above.

```sh
python3 -B -m unittest discover -s line-2/tools/bundle-refresh -p 'test_*.py' -v
```

Coverage is the exact measured inventory, never a complete wallet audit. Unknown spenders, Permit2 subpermissions, unused signatures, custom authorizations, other tokens and chains remain unknown. RPC evidence and reference headers are trusted inputs, not state proofs. Age is relative to the caller's reference, which can itself be old; later headers alone prove neither ancestry nor canonicality. Nothing grants transaction authority or promises future execution. Neither tool opens keys or wallets, reads environment variables, signs, sends, pays, posts or deploys.
