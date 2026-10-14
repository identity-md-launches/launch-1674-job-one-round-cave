# Calldata Lens

Decode the argument bytes of a saved Ethereum call rehearsal using an explicitly
chosen flat ABI layout. This complements the existing Return Lens: a worker can
read what a rehearsed call was asking for as well as what it returned, without
guessing the function name or ABI from a four-byte selector. Python 3.9+ standard
library only.

From the repository root, run this offline demonstration:

```sh
python3 -B line-4/tools/calldata-lens/calldata_lens.py demo
```

When tried on 2026-10-14 it printed `decoded`, the real ZTO target
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`, selector `0x18160ddd`, and an
empty argument list for the saved real `totalSupply()` rehearsal. The command
makes no network request.

For another saved Call Rehearsal observation, provide the reviewed ABI types for
the bytes *after* its selector:

```sh
python3 -B line-4/tools/calldata-lens/calldata_lens.py check path/to/observation.json --types address,uint256
```

Supported flat types are `uint8` through `uint256` and `int8` through `int256`
in eight-bit increments, `bool`, `address`, `bytes1` through `bytes32`, `bytes`,
and `string`. Pass an empty `--types ''` for a known no-argument function.
Arrays, tuples, aliases and fixed-point types are rejected. The selector is
reported as raw bytes only; it is not mapped to a name. Addresses and bytes are
hexadecimal; integers are decimal strings; strings require strict UTF-8.

The underlying rehearsal is strictly validated first, so the report keeps the
exact target, sender presence, calldata, native value, source and historical
block. Argument decoding requires canonical ABI offsets, widths, padding and
exact byte consumption. It rejects incomplete selectors, gaps, trailing bytes,
malformed dynamic data and noncanonical values.

Focused tests:

```sh
python3 -B -m unittest discover -s line-4/tools/calldata-lens -p 'test_*.py' -v
```

Seven tests passed on 2026-10-14, including the saved real ZTO no-argument
call, explicit address/amount values, selector non-inference, malformed
calldata and the offline CLI. Synthetic calldata used in tests is clearly only a
parser fixture, not a request to transfer a token.

The type list must come from a reviewed ABI. A result only says that historical
bytes fit those types; it does not prove the selector meaning, intended effect,
permissions, balances, state changes, gas, safety, chain authenticity or later
execution. No wallet, key, secret, environment variable, signature, transaction,
payment, post or deployment is read or used. Keep the adjacent `return-lens/`
and `call-changes/` folders when moving this tool; their reviewed decoders and
strict observation validator are reused without modification.
