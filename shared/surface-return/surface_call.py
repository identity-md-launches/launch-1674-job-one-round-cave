#!/usr/bin/env python3
"""Join proof-backed selector evidence with canonical call arguments and returns."""
import argparse
import json
from pathlib import Path
import sys

import surface_return as context

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calldata-lens'))
import calldata_lens as calldata

SCHEMA = 'surface-call-context-v1'
LIMITS = (
    'The signature and return layout are reviewer choices, not an authenticated ABI. '
    'A selector collision or unreachable pattern can match. Code inclusion is relative '
    'to the supplied header; its authenticity is not established by this tool. Call '
    'arguments and returns are historical RPC claims, not locally executed or proved '
    'state effects. No freshness, balance availability for spending, permissions, gas, '
    'routing, safety or future execution is established. Nothing is signed or sent.'
)


def argument_types(signature):
    """Use precisely the argument layout named in the explicit canonical signature."""
    context.surface.signature_selector(signature)
    inner = signature[signature.index('(') + 1:-1]
    return calldata.types_argument(inner)


def evaluate(bundle, observation, signature, return_types, anchor_hash=None):
    types = argument_types(signature)
    # Reverify raw proof, exact block/target/selector, and raw return bytes first.
    joined = context.evaluate(bundle, observation, signature, return_types, anchor_hash)
    arguments = None
    argument_error = None
    try:
        decoded = calldata.decode_call(observation, types)
        arguments = decoded['arguments']
    except (ValueError, UnicodeError) as error:
        argument_error = str(error)
    checks = dict(joined['checks'], arguments_decoded=arguments is not None)
    aligned = all(checks.values())
    return {
        'schema': SCHEMA, 'verdict': 'aligned' if aligned else 'mismatch',
        'checks': checks, 'failed_checks': [key for key, value in checks.items() if not value],
        'chain_id': 1, 'target': joined['target'], 'signature': signature,
        'selector': joined['selector'], 'argument_types': types,
        'return_types': context.returns.layout(return_types),
        'call': context.returns.changes.validate(observation)['call'],
        'source': observation['source'],
        'code_block': joined['code_block'], 'call_block': joined['call_block'],
        'proof_anchor': joined['proof_anchor'],
        'state_inclusion_verified': joined['state_inclusion_verified'],
        'target_pattern_matches': joined['target_pattern_matches'],
        'decoded_arguments': arguments if aligned else None,
        'decoded_values': joined['decoded_values'] if aligned else None,
        'argument_error': argument_error,
        'input_sha256': {
            'proof_bundle': context.digest(bundle),
            'call_observation': context.digest(observation),
            'caller_choices': context.digest({'signature': signature,
                'argument_types': types, 'return_types': return_types, 'anchor_hash': anchor_hash}),
        },
        'limits': LIMITS,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='replay real ZTO PoolManager balance evidence offline')
    parser.add_argument('--bundle', help='raw Code Proof JSON within the workspace')
    parser.add_argument('--observation', help='raw Call Rehearsal JSON within the workspace')
    parser.add_argument('--signature', help='reviewer-selected canonical signature; flat types only')
    parser.add_argument('--types', help='reviewer-selected comma-separated flat return types')
    parser.add_argument('--anchor-hash', help='optional independently trusted execution block hash')
    args = parser.parse_args(argv)
    try:
        selected = [args.bundle, args.observation, args.signature, args.types]
        context.surface.require((args.demo and not any(selected) and not args.anchor_hash) or
                                (not args.demo and all(selected)),
                                'choose --demo or all four explicit inputs')
        if args.demo:
            bundle, _ = context.demo_inputs()
            observation = calldata.load(HERE / 'zto-pool-balance-call.json')
            signature, types = 'balanceOf(address)', ['uint256']
        else:
            bundle = context.surface.ancestry.read_json(args.bundle)
            observation = calldata.load(args.observation)
            signature, types = args.signature, args.types.split(',')
        result = evaluate(bundle, observation, signature, types, args.anchor_hash)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result['verdict'] == 'aligned' else 2
    except (ValueError, KeyError, TypeError, OSError, OverflowError, AttributeError,
            IndexError, RecursionError) as error:
        print(json.dumps({'schema': SCHEMA, 'verdict': 'invalid', 'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
