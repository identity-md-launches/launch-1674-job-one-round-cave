#!/usr/bin/env python3
"""Withhold an entire unsigned revoke bundle unless its inventory is rechecked.

Standard-library, offline review. No signing, sending, wallet or key access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'draft-bundle'))
import draft_bundle as bundles

drafts = bundles.drafts
gate = drafts.gate
lens = gate.lens
changes = gate.changes


def digest(value):
    return hashlib.sha256(bundles.canonical(value).encode()).hexdigest()


def check(bundle, before, policy, after, reference, maximum_age_blocks):
    lens.require(type(maximum_age_blocks) is int and maximum_age_blocks >= 0,
                 'maximum age must be a nonnegative integer number of blocks')
    # Reconstruct from raw evidence before trusting any supplied handoff.
    review = bundles.check(bundle, before, policy)
    old, new = changes.flatten(before), changes.flatten(after)
    comparison = changes.compare(before, after)
    lens.require(new['block_number'] > old['block_number'],
                 'recheck must be at a later block than the reviewed inventory')
    gate.exact_keys(reference, ('schema', 'chain_id', 'source', 'block'), 'reference')
    lens.require(reference['schema'] == 'permission-reference-block-v1' and
                 type(reference['chain_id']) is int and reference['chain_id'] == 1,
                 'reference must select Ethereum chain 1')
    lens.require(reference['source'] in lens.PUBLIC_ENDPOINTS, 'invalid reference source')
    gate.exact_keys(reference['block'], ('number', 'hash', 'timestamp'), 'reference block')
    head = lens.header(reference['block'])
    age = lens.quantity(head['number']) - new['block_number']
    lens.require(age >= 0, 'reference precedes the inventory recheck')
    # Flatten already parses and binds every observation timestamp in a bundle.
    observations = after['observations'] if after.get('schema') == changes.BUNDLE_SCHEMA else [after]
    timestamp = lens.quantity(observations[0]['block']['timestamp'])
    lens.require(lens.quantity(head['timestamp']) >= timestamp,
                 'reference timestamp precedes the inventory recheck')
    if age == 0:
        lens.require(head['hash'] == new['block_hash'] and
                     lens.quantity(head['timestamp']) == timestamp,
                     'same-height reference differs from rechecked block')

    _, _, _, limits = gate.policy(policy)
    expected, _ = bundles.expected_bundle(before, policy)
    candidates = {(row['owner'], row['spender']): row for row in expected['drafts']}
    missing = sorted(set(old['pairs']) - set(new['pairs']))
    extra = sorted(set(new['pairs']) - set(old['pairs']))
    issues, pairs = [], []
    for pair in sorted(set(old['pairs']) | set(new['pairs'])):
        current = new['pairs'].get(pair)
        previous = old['pairs'].get(pair)
        ceiling = limits.get(pair, 0)
        if current is None:
            status = 'not_rechecked'
        elif previous is None:
            status = 'outside_reviewed_coverage'
        elif pair in candidates:
            amount = int(current['allowance_raw'])
            status = ('permission_cleared' if amount == 0 else
                      'within_reviewed_limit' if amount <= ceiling else
                      'same_active_permission' if current['allowance_raw'] == candidates[pair]['allowance_raw'] else
                      'changed_active_permission')
        else:
            status = ('new_policy_violation' if int(current['allowance_raw']) > ceiling else
                      'still_within_reviewed_limit')
        row = {
            'owner': pair[0], 'spender': pair[1], 'status': status,
            'reviewed_candidate': pair in candidates,
            'policy_limit_raw': str(ceiling),
            'previous_allowance_raw': None if previous is None else previous['allowance_raw'],
            'current_allowance_raw': None if current is None else current['allowance_raw'],
            'current_balance_raw': None if current is None else current['balance_raw'],
        }
        pairs.append(row)
        if status not in ('same_active_permission', 'still_within_reviewed_limit'):
            issues.append(row)
    reasons = []
    if not review['matches_reviewed_bundle']:
        reasons.append('original_bundle_not_reviewed_complete')
    if missing or extra:
        reasons.append('inventory_coverage_changed')
    if issues:
        reasons.append('permissions_require_new_review')
    if age > maximum_age_blocks:
        reasons.append('stale_inventory_recheck')
    accepted = not reasons
    return {
        'schema': 'permission-bundle-refresh-report-v1',
        'status': ('release_bundle_for_owner_review' if accepted and candidates else
                   'no_reviewed_candidates' if accepted else 'withhold_entire_bundle'),
        'accepted': accepted, 'withholding_reasons': reasons,
        'chain_id': new['chain_id'], 'token_address': new['token_address'],
        'previous_block_number': old['block_number'], 'current_block_number': new['block_number'],
        'current_block_hash': new['block_hash'],
        'reference_block_number': lens.quantity(head['number']), 'reference_block_hash': head['hash'],
        'age_blocks': age, 'maximum_age_blocks': maximum_age_blocks,
        'reviewed_candidate_count': len(candidates), 'current_pair_count': len(new['pairs']),
        'coverage_exact': not missing and not extra,
        'bundle_review': review, 'pair_reviews': pairs,
        'balance_changed_pairs': comparison['balance_changed_pairs'],
        'input_sha256': {name: digest(value) for name, value in
                         [('bundle', bundle), ('before', before), ('policy', policy),
                          ('after', after), ('reference', reference)]},
        'owner_review_bundle': bundle if accepted else None,
        'complete_wallet_audit': False,
        'limitations': [
            'All-or-nothing release covers only the exact supplied measured inventory, never a whole wallet.',
            'Original ceilings apply to rechecked pairs; the original policy block interval applies to initial review only.',
            'Changed, cleared or newly violating permissions require a new review; no partial bundle is released.',
            'Balance changes alone do not change permission. Candidate balances remain historical; current balances are reported separately.',
            'Age is relative to the supplied reference, not wall-clock time or the current chain tip.',
            'RPC evidence is trusted, not state proofs; later headers alone do not prove ancestry or canonicality.',
            'Permit2, unknown spenders, unused signatures and custom authorizations remain outside coverage.',
            'Release requires an independent owner decision; no authorization, simulation, signing or transaction sending occurs.',
        ],
    }


def demo_inputs():
    before = gate.load(drafts.DEFAULT_OBSERVATION)
    policy = gate.load(drafts.DEFAULT_POLICY)
    bundle, _ = bundles.expected_bundle(before, policy)
    return (bundle, before, policy, gate.load(HERE / 'live-after.json'),
            gate.load(HERE / 'live-reference.json'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'before', 'policy', 'after', 'reference'):
        parser.add_argument('--' + name, help='workspace JSON input')
    parser.add_argument('--maximum-age-blocks', type=int, help='inclusive caller-selected age limit')
    args = parser.parse_args(argv)
    try:
        paths = [args.bundle, args.before, args.policy, args.after, args.reference]
        demo = not any(paths) and args.maximum_age_blocks is None
        lens.require(demo or (all(paths) and args.maximum_age_blocks is not None),
                     'provide all five inputs and --maximum-age-blocks, or none for the historical demo')
        inputs = demo_inputs() if demo else tuple(gate.load(path) for path in paths)
        result = check(*inputs, 0 if demo else args.maximum_age_blocks)
        result['demonstration'] = demo
        print(json.dumps(result, indent=2))
        return 0 if result['accepted'] else 3
    except (ValueError, KeyError, TypeError, OSError, OverflowError, RecursionError, IndexError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
