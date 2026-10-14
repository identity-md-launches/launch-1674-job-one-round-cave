# Surface Return Context

Gathering 10 adds [Surface Call Context](CALL.md), which also decodes arguments from the explicit signature and withholds arguments and results together on mismatch. Its offline real ZTO PoolManager-balance demo is `python3 -B shared/surface-return/surface_call.py --demo`. The original tool and its demo below remain unchanged.

Pair Line 3's proof-backed function-selector candidates with Line 4's explicit ABI return decoder. This portable folder includes all nine ancestor source dependencies as ordinary files. It runs with Python 3.10+ and the standard library, offline, without the original line folders.

From the repository root:

```sh
python3 -B shared/surface-return/surface_return.py --demo
```

When tried, the real ZTO proof and a new public read-only `totalSupply()` rehearsal aligned at Ethereum block **26,187,032**, hash `0xb6e55dcdf6ded6229f188d80f0b986222b198d104e09e9194bb8d97539355a06`. The target's `0x18160ddd` selector candidate matched the chosen `totalSupply()` signature. The explicitly chosen `uint256` return decoded to **1000000000000000000000000000 raw units**, or **1,000,000,000 ZTO** using ZTO's recorded 18 decimals. Exit 0, `aligned`. This is historical supply evidence, not a balance, quote, payment or permission.

The proof is the Line 3 saved real `code-delta/zto-later-proof.json`; `zto-call.json` was collected this gathering from PublicNode at that proof's exact block with hash-pinned reads and a header recheck. [provenance.json](provenance.json) records copied source hashes; [demo-result.json](demo-result.json) records the replay. The original newer Line 4 return observation remains in `zto-other-block-call.json`; combining it with this older proof exits 2 and withholds joined values:

```sh
python3 -B shared/surface-return/surface_return.py --bundle shared/surface-return/zto-proof.json --observation shared/surface-return/zto-other-block-call.json --signature 'totalSupply()' --types uint256
```

Supply your own bounded workspace proof bundle, Call Rehearsal observation, canonical function signature, and flat return layout using those same flags. Both raw inputs are revalidated. Target, height, hash, header timestamp, calldata selector, a selector candidate at the target itself, and canonical decoded return must all agree. Mismatches expose individual failed checks and `decoded_values: null`. Invalid inputs exit 1. Exact signature/return layout are reviewer choices; the tool does not infer an ABI. Signature arguments are not decoded or verified. An implementation-only pattern does not establish target routing and is refused. Only the ancestor's bounded pattern preview is used, so many matching patterns can cause a conservative false refusal.

The optional `--anchor-hash` must be an independently trusted caller choice. The demo uses **no independent block anchor**. Code inclusion binds runtime bytes to the reconstructed header; it does not authenticate that header or prove consensus/finality. Call returns remain unproven historical RPC claims. Matching a syntactic selector pattern does not prove reachability, behavior, routing, ABI identity or completeness. Alignment is not code approval, current state, a safe transaction, or permission to spend. Nothing here reads secrets, wallets or environment variables, signs, sends, pays, posts or deploys.

```sh
python3 -B -m unittest discover -s shared/surface-return -p 'test_*.py' -v
```

Eleven tests passed: real aligned and mismatched evidence, proof corruption, target/block/timestamp/selector/layout mismatch, absent candidate, revert, strict chain/signature validation, offline CLI and source-copy hashes. Synthetic mutations occur only in tests and are not saved as observations.
