#!/usr/bin/env python3
"""Read every previously measured ZTO pair and a reference; save no partial read.

Only allowlisted read-only RPC methods. Never opens a wallet or sends a transaction.
"""
import argparse
import json
from pathlib import Path
import sys

import bundle_refresh as tool

ASSIGNMENT_RPC = 'http://127.0.0.1:38413/rpc/1'


class ReadOnlyRPC(tool.lens.RPC):
    def __init__(self, endpoint):
        tool.lens.require(endpoint in tool.lens.PUBLIC_ENDPOINTS | {ASSIGNMENT_RPC},
                          'use a documented public RPC or this assignment endpoint')
        super().__init__(tool.lens.PUBLIC_RPC)
        self.endpoint = endpoint


def capture(endpoint, before, policy):
    rpc = ReadOnlyRPC(endpoint)
    after = tool.changes.refresh(rpc, before, 'finalized')
    reference = {
        'schema': 'permission-reference-block-v1', 'chain_id': 1,
        'source': tool.lens.PUBLIC_RPC if endpoint == ASSIGNMENT_RPC else endpoint,
        'block': tool.lens.header(rpc.call('eth_getBlockByNumber', ['finalized', False])),
    }
    bundle, _ = tool.bundles.expected_bundle(before, policy)
    report = tool.check(bundle, before, policy, after, reference, 8)
    return after, reference, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rpc', choices=sorted(tool.lens.PUBLIC_ENDPOINTS | {ASSIGNMENT_RPC}),
                        default=tool.lens.PUBLIC_RPC)
    parser.add_argument('--output', required=True, help='new directory inside this tool folder')
    args = parser.parse_args()
    try:
        output = tool.lens.workspace_path(args.output)
        tool.lens.require(output.is_relative_to(tool.HERE) and not output.exists(),
                          'output must be a new directory inside this tool folder')
        before = tool.gate.load(tool.drafts.DEFAULT_OBSERVATION)
        policy = tool.gate.load(tool.drafts.DEFAULT_POLICY)
        values = tool.lens.run_bounded(capture, (args.rpc, before, policy), timeout=55)
        encoded = [json.dumps(value, indent=2) + '\n' for value in values]
        tool.lens.require(all(len(value.encode()) < 100000 for value in encoded), 'output exceeds limit')
        output.mkdir()
        for name, value in zip(('live-after.json', 'live-reference.json', 'live-review.json'), encoded):
            with (output / name).open('x') as stream:
                stream.write(value)
        print(json.dumps({'status': values[2]['status'], 'accepted': values[2]['accepted'],
                          'pairs': values[2]['current_pair_count'],
                          'block': values[2]['current_block_number'], 'age': values[2]['age_blocks']}))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, TimeoutError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
