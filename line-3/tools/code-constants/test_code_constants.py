"""Real proof replays and explicitly synthetic bytecode adversaries."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
import code_constants as constants

FOLDER = Path(__file__).resolve().parent
ADDRESS = bytes.fromhex(constants.lens.ZTO[2:])


def evidence(token='zto'):
    return constants.ancestry.read_json(FOLDER.parent / 'code-delta' / (token + '-later-proof.json'))


def scan(code):
    return constants.scan(code, constants.lens.ZTO)


class ConstantsTests(unittest.TestCase):
    def test_real_zto_imd_proofs(self):
        expected = {'zto': (0, 0, 0), 'imd': (82, 5, 8)}
        for token, counts in expected.items():
            result = constants.inspect(evidence(token))
            runtime = result['runtimes'][0]
            self.assertEqual(tuple(runtime['literal_occurrence_counts'][k]
                                   for k in ('address-mask', 'small-integer', 'address-shaped')), counts)
            self.assertTrue(result['proof']['state_inclusion_verified'])
            self.assertEqual(result['proof']['anchor'], 'unanchored-rpc-header')
            self.assertFalse(result['dependencies_verified'])
            self.assertFalse(result['reachability_verified'])

    def test_push20_and_padded_push32_group_together(self):
        result = scan(b'\x73' + ADDRESS + b'\x7f' + bytes(12) + ADDRESS)
        group = result['literal_preview'][0]
        self.assertEqual(group['literal'], constants.lens.ZTO)
        self.assertTrue(group['equals_runtime_address'])
        self.assertEqual(group['occurrence_count'], 2)
        self.assertEqual([p['pc'] for p in group['occurrence_preview']], [0, 21])
        self.assertEqual([p['push_bytes'] for p in group['occurrence_preview']], [20, 32])

    def test_mask_zero_and_integer_not_address_shaped(self):
        code = b''.join(b'\x73' + value.to_bytes(20, 'big')
                        for value in (0, constants.ADDRESS_MASK, 123, 2**64))
        self.assertEqual(scan(code)['literal_occurrence_counts'],
                         {'zero': 1, 'address-mask': 1, 'small-integer': 1, 'address-shaped': 1})

    def test_push32_high_bits_excluded(self):
        self.assertEqual(scan(b'\x7f' + b'\x01' + bytes(11) + ADDRESS)['unique_literal_count'], 0)

    def test_push_operands_do_not_become_instructions(self):
        code = b'\x7f' + (b'\x73' + ADDRESS).ljust(32, b'\xff')
        self.assertEqual(scan(code)['unique_literal_count'], 0)

    def test_truncated_pushes_are_not_literals(self):
        for opcode, length in ((0x73, 20), (0x7f, 32)):
            for count in range(length):
                result = scan(bytes([opcode]) + b'\x73' * count)
                self.assertEqual(result['unique_literal_count'], 0)
                self.assertEqual(result['truncated_relevant_push_count'], 1)

    def test_address_eq_adjacency_and_unreachable_code(self):
        group = scan(b'\x00\x73' + ADDRESS + b'\x30\x14')['literal_preview'][0]
        self.assertTrue(group['occurrence_preview'][0]['followed_by_address_eq'])
        self.assertEqual(group['occurrence_preview'][0]['pc'], 1)
        for tail in (b'\x30', b'\x14\x30', b'\x60\x30\x14', b'\x30\x15'):
            group = scan(b'\x73' + ADDRESS + tail)['literal_preview'][0]
            self.assertFalse(group['occurrence_preview'][0]['followed_by_address_eq'])

    def test_metadata_annotated_not_discarded(self):
        # CBOR with Solidity version and byte-string containing a literal.
        prefix = bytes.fromhex('a264736f6c63430008196469706673') + b'\x55'
        metadata = prefix + b'\x73' + ADDRESS
        result = scan(b'\x00' + metadata + len(metadata).to_bytes(2, 'big'))
        self.assertIsNotNone(result['recognized_solidity_metadata'])
        self.assertTrue(result['literal_preview'][0]['occurrence_preview'][0]['overlaps_recognized_metadata'])

    def test_bounded_occurrences_and_groups(self):
        repeated = scan((b'\x73' + ADDRESS) * 200)
        group = repeated['literal_preview'][0]
        self.assertEqual(group['occurrence_count'], 200)
        self.assertEqual(len(group['occurrence_preview']), 32)
        self.assertEqual(group['omitted_occurrence_count'], 168)
        distinct = scan(b''.join(b'\x73' + (2**80 + i).to_bytes(20, 'big') for i in range(200)))
        self.assertEqual(distinct['unique_literal_count'], 200)
        self.assertEqual(len(distinct['literal_preview']), 32)
        self.assertEqual(distinct['omitted_unique_literal_count'], 168)

    def test_maximum_runtime_output_bounded(self):
        code = b''.join(b'\x73' + (2**80 + i).to_bytes(20, 'big')
                        for i in range(constants.lens.MAX_CODE // 21))
        self.assertLess(len(json.dumps(scan(code))), 60000)
        with self.assertRaises(ValueError):
            scan(b'\0' * (constants.lens.MAX_CODE + 1))

    def test_proof_corruption_and_consistent_runtime_forgery_refused(self):
        for mutation in ('header', 'proof', 'runtime'):
            bundle = evidence()
            if mutation == 'header':
                bundle['header_rlp'] = bundle['header_rlp'][:-2] + 'ff'
            elif mutation == 'proof':
                bundle['proofs'][0]['accountProof'].pop()
            else:
                node = bundle['observation']['nodes'][0]
                code = b'\x73' + ADDRESS
                node.update(code='0x' + code.hex(), code_bytes=len(code), code_hash=constants.lens.digest(code))
                bundle['observation']['effective_code_hash'] = node['code_hash']
                bundle['proofs'][0]['codeHash'] = node['code_hash']
            with self.assertRaises(ValueError):
                constants.inspect(bundle)

    def test_caller_anchor_equality_does_not_authenticate(self):
        bundle = evidence()
        result = constants.inspect(bundle, bundle['observation']['block']['hash'])
        self.assertEqual(result['proof']['anchor'], 'caller-supplied-block-hash')
        self.assertFalse(result['anchor_authenticity_verified'])
        old = constants.ancestry.read_json(FOLDER.parent / 'code-proof/zto-proof.json')
        with self.assertRaises(ValueError):
            constants.inspect(bundle, old['observation']['block']['hash'])

    def test_beacon_dedup_and_unproven_call_warning(self):
        spec = importlib.util.spec_from_file_location('proof_fixture', FOLDER.parent / 'code-proof/test_code_proof.py')
        fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture)
        result = constants.inspect(fixture.synthetic_beacon_bundle())
        self.assertEqual(len(result['runtimes']), 2)
        runtime = next(r for r in result['runtimes'] if r['address'] == constants.lens.IMD)
        self.assertEqual(set(runtime['roles']), {'beacon', 'candidate-path'})
        self.assertEqual(result['proof']['unproven_beacon_call_results'], [constants.lens.IMD])

    def test_input_duplicate_keys_and_workspace_boundary(self):
        with self.assertRaises(ValueError):
            json.loads('{"x":1,"x":2}', object_pairs_hook=constants.ancestry.no_duplicates)
        with self.assertRaises(ValueError):
            constants.ancestry.read_json(Path.cwd().parent / 'outside.json')

    def test_cli_success_and_no_partial_json_on_failure(self):
        base = [sys.executable, '-B', str(FOLDER / 'code_constants.py'), '--bundle',
                str(FOLDER.parent / 'code-delta/zto-later-proof.json')]
        success = subprocess.run(base, capture_output=True, text=True, timeout=30)
        self.assertEqual(success.returncode, 0)
        self.assertEqual(json.loads(success.stdout)['schema'], 'code-constants-result-v1')
        old = constants.ancestry.read_json(FOLDER.parent / 'code-proof/zto-proof.json')
        failure = subprocess.run(base + ['--anchor-hash', old['observation']['block']['hash']],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(failure.returncode, 1)
        self.assertEqual(failure.stdout, '')

    def test_demo(self):
        import demo
        self.assertTrue(demo.main()['demonstration_passed'])


if __name__ == '__main__':
    unittest.main()
