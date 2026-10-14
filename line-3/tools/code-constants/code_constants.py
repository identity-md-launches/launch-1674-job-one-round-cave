#!/usr/bin/env python3
"""Proof-backed inventory of address-width literals; no dependency inference."""
import argparse
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / 'code-surface'))
import code_surface as surface

ancestry, proof, lens = surface.ancestry, surface.proof, surface.lens
PREVIEW = 32
ADDRESS_MASK = 2**160 - 1


def scan(code, own_address):
    """Scan complete PUSH20 / zero-extended PUSH32 operands at instruction boundaries.

    Small integers and masks are retained as separate categories. A nearby opcode
    is context only: it does not demonstrate that the literal supplies that opcode.
    """
    own_address = lens.address(own_address)
    decoded = surface.instructions(code)
    metadata = surface.opcodes.solidity_metadata(code)
    groups = {}
    counts = {'zero': 0, 'address-mask': 0, 'small-integer': 0, 'address-shaped': 0}
    truncated = 0
    for index, (pc, opcode, operand, complete) in enumerate(decoded):
        if opcode not in (0x73, 0x7f):
            continue
        if not complete:
            truncated += 1
            continue
        if opcode == 0x7f and operand[:12] != bytes(12):
            continue
        value = int.from_bytes(operand, 'big')
        category = ('zero' if value == 0 else 'address-mask' if value == ADDRESS_MASK
                    else 'small-integer' if value < 2**64 else 'address-shaped')
        counts[category] += 1
        literal = '0x' + value.to_bytes(20, 'big').hex()
        if literal not in groups:
            groups[literal] = {'literal': literal, 'category': category,
                               'equals_runtime_address': literal == own_address,
                               'occurrence_count': 0, 'occurrence_preview': []}
        group = groups[literal]
        group['occurrence_count'] += 1
        following = decoded[index + 1:index + 5]
        equality = len(following) >= 2 and [item[1] for item in following[:2]] == [0x30, 0x14]
        if len(group['occurrence_preview']) < PREVIEW:
            group['occurrence_preview'].append({
                'pc': pc, 'push_bytes': len(operand),
                'overlaps_recognized_metadata': bool(metadata and pc + 1 + len(operand) > metadata['start']),
                'followed_by_address_eq': equality,
                'following_instructions': [{'pc': next_pc, 'opcode': hex(op),
                                            'operand': '0x' + data.hex(), 'complete': valid}
                                           for next_pc, op, data, valid in following],
            })
    # Largest possible output remains bounded, even for maximum-size hostile code.
    # Keep exact category/unique/occurrence counts while bounding group previews.
    ordered = sorted(groups.values(), key=lambda group: group['occurrence_preview'][0]['pc'])
    for group in ordered:
        group['omitted_occurrence_count'] = group['occurrence_count'] - len(group['occurrence_preview'])
    return {'recognized_solidity_metadata': metadata,
            'literal_occurrence_counts': counts, 'unique_literal_count': len(ordered),
            'literal_preview': ordered[:PREVIEW],
            'omitted_unique_literal_count': max(0, len(ordered) - PREVIEW),
            'truncated_relevant_push_count': truncated}


def inspect(bundle, anchor_hash=None):
    checked = proof.verify(bundle, anchor_hash)
    observation = bundle['observation']
    runtimes, seen = [], {}
    for node in observation['nodes']:
        for item, role in ((node, 'candidate-path'), (node.get('beacon'), 'beacon')):
            if item is None:
                continue
            address = lens.address(item['address'])
            if address in seen:
                if role not in seen[address]['roles']:
                    seen[address]['roles'].append(role)
                continue
            result = {'address': address, 'code_hash': lens.fixed_hex(item['code_hash'], 32),
                      'roles': [role], 'runtime_bytes': len(lens.code_bytes(item['code']))}
            result.update(scan(lens.code_bytes(item['code']), address))
            seen[address] = result
            runtimes.append(result)
    return {'schema': 'code-constants-result-v1', 'chain_id': 1,
            'target': checked['target'], 'code_block': ancestry.block_identity(observation['block']),
            'proof': checked, 'runtimes': runtimes,
            'anchor_authenticity_verified': False, 'dependencies_verified': False,
            'reachability_verified': False, 'semantic_safety_verified': False,
            'scope': 'PUSH20 and zero-extended PUSH32 literal inventory in proof-backed historical runtime. '
                     'Address-shaped values can be numbers, masks, data or unreachable code. '
                     'Following instructions are syntactic context, not stack dataflow. '
                     'ADDRESS EQ adjacency can resemble a library guard but proves no guard semantics. '
                     'Other constant encodings, storage-loaded and computed addresses are not covered. '
                     'No external account identity, dependency, source equivalence, routing, consensus, '
                     'finality, current code or contract safety is verified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, help='workspace-local raw Code Proof bundle')
    parser.add_argument('--anchor-hash', help='independently trusted execution block hash')
    args = parser.parse_args()
    try:
        result = inspect(ancestry.read_json(args.bundle), args.anchor_hash)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, AttributeError,
            IndexError, RecursionError) as error:
        print('Code Constants: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
