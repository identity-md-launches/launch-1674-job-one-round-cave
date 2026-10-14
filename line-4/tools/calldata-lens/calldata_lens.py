#!/usr/bin/env python3
"""Decode explicit flat ABI calldata arguments from a saved call rehearsal."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'call-changes'))
sys.path.insert(0, str(HERE.parent / 'return-lens'))
import call_changes as changes
import return_lens

SCHEMA = 'calldata-lens-v1'
LIMITS = (
    'Argument types are supplied by the reviewer and are not inferred from the selector. '
    'A decoded calldata payload does not authenticate an ABI, establish intended effects, '
    'permissions, balances, gas, safety, current state, or future execution. It makes no '
    'network request and does not sign, send, pay, post, or deploy anything.'
)


def types_argument(value):
    if value == '':
        return []
    return return_lens.layout(value.split(','))


def layout(types):
    changes.core.require(isinstance(types, list), 'ABI types must be a list')
    return [] if not types else return_lens.layout(types)


def decode_call(observation, types):
    """Validate inherited evidence, then decode bytes after its 4-byte selector."""
    types = layout(types)
    checked = changes.validate(observation)
    calldata = checked['call']['data']
    raw = bytes.fromhex(calldata[2:])
    changes.core.require(len(raw) >= 4, 'calldata must include a four-byte selector')
    selector = '0x' + raw[:4].hex()
    encoded_arguments = '0x' + raw[4:].hex()
    if not types:
        changes.core.require(encoded_arguments == '0x', 'no-argument layout has trailing calldata')
        arguments = []
    else:
        arguments = return_lens.decode(encoded_arguments, types)
    return {
        'schema': SCHEMA,
        'verdict': 'decoded',
        'source': observation['source'],
        'chain_id': 1,
        'block': changes.core.header(observation['block']),
        'call': checked['call'],
        'selector': selector,
        'types': types,
        'arguments': arguments,
        'limits': LIMITS,
    }


def load(path):
    return changes.load_observation(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='decode the no-argument real ZTO totalSupply() call offline')
    check = commands.add_parser('check', help='decode arguments from a saved Call Rehearsal observation')
    check.add_argument('observation')
    check.add_argument('--types', default='',
                       help='explicit comma-separated flat ABI types after the selector')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            observation = load(HERE.parent / 'call-rehearsal' / 'zto-observation.json')
            types = []
        else:
            observation = load(args.observation)
            types = types_argument(args.types)
        print(json.dumps(decode_call(observation, types), indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError, RecursionError) as exc:
        print(json.dumps({'schema': SCHEMA, 'verdict': 'inconclusive', 'error': str(exc)}),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
