import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

import bundle_refresh as tool


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.bundle, self.before, self.policy, self.after, self.reference = copy.deepcopy(tool.demo_inputs())

    def check(self, limit=0):
        return tool.check(self.bundle, self.before, self.policy, self.after, self.reference, limit)

    def set_allowance(self, pair, amount):
        for observation in self.after['observations']:
            for row in observation['raw']['allowances']:
                if (row['owner'], row['spender']) == pair:
                    row['result'] = '0x' + format(amount, '064x')
                    return
        self.fail('pair not found')

    def test_real_inventory_and_digest_binding(self):
        result = self.check()
        self.assertTrue(result['accepted'])
        self.assertEqual(result['reviewed_candidate_count'], 3)
        self.assertEqual(result['current_pair_count'], 19)
        self.assertEqual(result['age_blocks'], 0)
        self.assertEqual(result['owner_review_bundle'], self.bundle)
        self.assertFalse(result['complete_wallet_audit'])
        self.assertEqual(result['input_sha256']['after'], tool.digest(self.after))

    def test_bundle_omission_duplicate_tampering_and_anchor(self):
        original = copy.deepcopy(self.bundle)
        for mutation in ('omit', 'duplicate', 'calldata', 'anchor'):
            with self.subTest(mutation=mutation):
                self.bundle = copy.deepcopy(original)
                if mutation == 'omit':
                    self.bundle['drafts'].pop()
                elif mutation == 'duplicate':
                    self.bundle['drafts'][1] = copy.deepcopy(self.bundle['drafts'][0])
                elif mutation == 'calldata':
                    self.bundle['drafts'][0]['transaction']['data'] = '0x095ea7b3'
                else:
                    self.bundle['chain_id'] = True
                result = self.check()
                self.assertFalse(result['accepted'])
                self.assertIsNone(result['owner_review_bundle'])
                self.assertIn('original_bundle_not_reviewed_complete', result['withholding_reasons'])

    def test_candidate_changed_cleared_or_within_limit(self):
        row = self.bundle['drafts'][0]
        pair = row['owner'], row['spender']
        for amount, status in [(int(row['allowance_raw']) - 1, 'changed_active_permission'),
                               (0, 'permission_cleared')]:
            self.set_allowance(pair, amount)
            result = self.check()
            self.assertFalse(result['accepted'])
            self.assertIsNone(result['owner_review_bundle'])
            self.assertEqual(next(x for x in result['pair_reviews'] if
                                  (x['owner'], x['spender']) == pair)['status'], status)

    def test_new_violation_blocks_original_bundle(self):
        measured = tool.changes.flatten(self.after)
        pair = next(pair for pair, row in measured['pairs'].items() if row['allowance_raw'] == '0')
        self.set_allowance(pair, 1)
        result = self.check()
        self.assertFalse(result['accepted'])
        self.assertIn('new_policy_violation', [row['status'] for row in result['pair_reviews']])

    def test_candidate_reduced_to_nonzero_policy_ceiling(self):
        row = self.bundle['drafts'][0]
        pair = row['owner'], row['spender']
        self.policy['pairs'] = [{'owner': pair[0], 'spender': pair[1], 'maximum_allowance_raw': '5'}]
        self.bundle, _ = tool.bundles.expected_bundle(self.before, self.policy)
        self.set_allowance(pair, 5)
        result = self.check()
        self.assertFalse(result['accepted'])
        self.assertIn('within_reviewed_limit', [r['status'] for r in result['pair_reviews']])

    def test_missing_pair_including_non_candidate(self):
        candidate_pairs = {(r['owner'], r['spender']) for r in self.bundle['drafts']}
        observations = self.after['observations']
        # Drop a whole valid one-owner observation that contains no candidate.
        index = next(i for i, obs in enumerate(observations) if not any(
            (r['owner'], r['spender']) in candidate_pairs for r in obs['raw']['allowances']))
        observations.pop(index)
        result = self.check()
        self.assertFalse(result['coverage_exact'])
        self.assertFalse(result['accepted'])
        self.assertIn('not_rechecked', [row['status'] for row in result['pair_reviews']])

    def test_extra_pair_refused(self):
        obs = self.after['observations'][0]
        # Use a real spender from the saved inventory, with synthetic evidence only in this test.
        other = next(r['spender'] for o in self.after['observations'] for r in o['raw']['allowances']
                     if r['spender'] not in obs['query']['spenders'])
        owner = obs['query']['owner']
        obs['query']['spenders'].append(other)
        obs['raw']['allowances'].append({'owner': owner, 'spender': other,
            'data': '0xdd62ed3e' + tool.lens.address_arg(owner) + tool.lens.address_arg(other),
            'result': '0x' + '0' * 64})
        result = self.check()
        self.assertFalse(result['accepted'])
        self.assertIn('outside_reviewed_coverage', [r['status'] for r in result['pair_reviews']])

    def test_balance_change_does_not_erase_permission(self):
        for obs in self.after['observations']:
            for row in obs['raw']['balances']:
                row['result'] = '0x' + '0' * 63 + '1'
        result = self.check()
        self.assertTrue(result['accepted'])
        self.assertGreater(result['balance_changed_pairs'], 0)
        self.assertTrue(all(row['current_balance_raw'] == '1' for row in result['pair_reviews']))
        self.assertEqual(result['owner_review_bundle'], self.bundle)

    def test_age_boundary_and_refusal(self):
        self.reference['block']['number'] = hex(int(self.reference['block']['number'], 16) + 8)
        self.reference['block']['timestamp'] = hex(int(self.reference['block']['timestamp'], 16) + 96)
        # Synthetic reference for inclusive-boundary test, never delivered as live evidence.
        self.assertTrue(self.check(8)['accepted'])
        result = self.check(7)
        self.assertFalse(result['accepted'])
        self.assertIn('stale_inventory_recheck', result['withholding_reasons'])
        self.assertIsNone(result['owner_review_bundle'])

    def test_reference_identity_and_limits(self):
        original = copy.deepcopy(self.reference)
        for key, value in [('schema', 'other'), ('chain_id', True), ('source', 'https://other.example')]:
            self.reference = copy.deepcopy(original)
            self.reference[key] = value
            with self.assertRaises(ValueError):
                self.check()
        self.reference = copy.deepcopy(original)
        self.reference['block']['hash'] = '0x' + '1' * 64
        with self.assertRaises(ValueError):
            self.check()
        self.reference = copy.deepcopy(original)
        self.reference['block']['number'] = hex(int(original['block']['number'], 16) - 1)
        with self.assertRaises(ValueError):
            self.check()
        self.reference = copy.deepcopy(original)
        self.reference['block']['timestamp'] = hex(int(original['block']['timestamp'], 16) - 1)
        with self.assertRaises(ValueError):
            self.check()
        self.reference = original
        for limit in (True, -1, 0.0, '0'):
            with self.assertRaises(ValueError):
                self.check(limit)

    def test_same_block_older_and_conflicting_inventory(self):
        self.after = copy.deepcopy(self.before)
        with self.assertRaises(ValueError):
            self.check()
        self.after = copy.deepcopy(tool.demo_inputs()[3])
        self.after['observations'][0]['block']['hash'] = '0x' + '1' * 64
        with self.assertRaises(ValueError):
            self.check()

    def test_insufficient_original_review_withheld(self):
        self.policy['minimum_block'] += 1
        self.policy['maximum_block'] += 1
        self.bundle, _ = tool.bundles.expected_bundle(self.before, self.policy)
        self.assertFalse(self.check()['accepted'])

    def test_no_candidates_remains_limited_review(self):
        measured = tool.changes.flatten(self.before)
        self.policy['pairs'] = [{'owner': pair[0], 'spender': pair[1],
                                'maximum_allowance_raw': row['allowance_raw']}
                               for pair, row in measured['pairs'].items()]
        self.bundle, _ = tool.bundles.expected_bundle(self.before, self.policy)
        result = self.check()
        self.assertEqual(result['status'], 'no_reviewed_candidates')
        self.assertTrue(result['accepted'])
        self.assertEqual(result['owner_review_bundle']['drafts'], [])
        self.assertFalse(result['complete_wallet_audit'])

    def test_input_digests_change_and_order_independence(self):
        original = self.check()
        self.bundle['drafts'].reverse()
        result = self.check()
        self.assertTrue(result['accepted'])
        self.assertNotEqual(original['input_sha256']['bundle'], result['input_sha256']['bundle'])
        self.assertEqual(original['input_sha256']['after'], result['input_sha256']['after'])

    def test_cli_and_workspace_guards(self):
        def invoke(args):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = tool.main(args)
            return code, out.getvalue(), err.getvalue()
        self.assertEqual(invoke([])[0], 0)
        self.assertEqual(invoke(['--maximum-age-blocks', '0'])[0], 1)
        scratch = Path.cwd() / 'test/scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            args = []
            for name, value in zip(('bundle', 'before', 'policy', 'after', 'reference'),
                                   (self.bundle, self.before, self.policy, self.after, self.reference)):
                path = Path(directory) / (name + '.json')
                path.write_text(json.dumps(value))
                args += ['--' + name, str(path)]
            args += ['--maximum-age-blocks', '0']
            self.assertEqual(invoke(args)[0], 0)
            bundle_path = Path(args[1])
            self.bundle['drafts'].pop()
            bundle_path.write_text(json.dumps(self.bundle))
            code, out, _ = invoke(args)
            self.assertEqual(code, 3)
            self.assertIsNone(json.loads(out)['owner_review_bundle'])
            bundle_path.write_text('{"schema":"one","schema":"two"}')
            self.assertIn('duplicate JSON key', invoke(args)[2])
            bundle_path.write_text(' ' * 98305)
            self.assertEqual(invoke(args)[0], 1)
            args[1] = str(Path.cwd().parent / 'never-open.json')
            self.assertIn('inside the current workspace', invoke(args)[2])


if __name__ == '__main__':
    unittest.main()
