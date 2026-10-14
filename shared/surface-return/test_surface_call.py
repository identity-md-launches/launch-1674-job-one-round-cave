"""Real saved evidence plus synthetic mutations, never saved as chain observations."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import surface_call as tool


class SurfaceCallTests(unittest.TestCase):
    def setUp(self):
        self.bundle, self.supply = tool.context.demo_inputs()
        self.call = tool.calldata.load(tool.HERE / 'zto-pool-balance-call.json')

    def evaluate(self, call=None, signature='balanceOf(address)', types=None):
        return tool.evaluate(self.bundle, self.call if call is None else call,
                             signature, ['uint256'] if types is None else types)

    def assert_withheld(self, result):
        self.assertEqual(result['verdict'], 'mismatch')
        self.assertIsNone(result['decoded_arguments'])
        self.assertIsNone(result['decoded_values'])

    def test_real_balance_and_exact_simulation_context(self):
        result = self.evaluate()
        self.assertEqual(result['verdict'], 'aligned')
        self.assertEqual(result['decoded_arguments'], [{'type': 'address', 'value':
            '0x000000000004444c5dc75cb358380d2e3de08a90'}])
        self.assertEqual(result['decoded_values'][0]['value'], '285939607966355541747129965')
        self.assertEqual(result['call'], self.call['call'])
        self.assertEqual(result['proof_anchor'], 'unanchored-rpc-header')

    def test_supply_has_no_arguments(self):
        result = self.evaluate(self.supply, 'totalSupply()')
        self.assertEqual(result['verdict'], 'aligned')
        self.assertEqual(result['decoded_arguments'], [])

    def test_truncated_trailing_and_noncanonical_arguments_withhold_both(self):
        original = self.call['call']['data']
        mutations = [original[:-2], original + '00' * 32,
                     original[:10] + '01' + original[12:]]
        for data in mutations:
            with self.subTest(data=data):
                call = copy.deepcopy(self.call)
                call['call']['data'] = data
                result = self.evaluate(call)
                self.assert_withheld(result)
                self.assertIn('arguments_decoded', result['failed_checks'])

    def test_no_arguments_signature_refuses_hidden_payload(self):
        call = copy.deepcopy(self.supply)
        call['call']['from'] = self.call['call']['from']
        call['call']['data'] += '00' * 32
        self.assert_withheld(self.evaluate(call, 'totalSupply()'))

    def test_signature_drives_types_and_never_infers_from_selector(self):
        self.assertEqual(tool.argument_types('probe(address,uint256,bytes)'),
                         ['address', 'uint256', 'bytes'])
        for signature in ('probe(uint)', 'probe(address[])', 'probe((address,uint256))',
                          'probe(function)', 'probe( address)'):
            with self.subTest(signature=signature), self.assertRaises(ValueError):
                tool.argument_types(signature)
        # The same 32 bytes can fit other layouts, but the chosen selector must agree.
        result = self.evaluate(signature='balanceOf(uint256)')
        self.assert_withheld(result)
        self.assertIn('call_selector_matches', result['failed_checks'])

    def test_target_and_each_block_dimension_withhold_arguments_too(self):
        for key, value in [('number', '0x1'), ('timestamp', '0x1'),
                           ('hash', '0x' + 'ab' * 32)]:
            call = copy.deepcopy(self.call)
            call['block'][key] = value
            self.assert_withheld(self.evaluate(call))
        call = copy.deepcopy(self.call)
        call['call']['to'] = tool.context.returns.core.TOKENS['IMD']
        self.assert_withheld(self.evaluate(call))

    def test_revert_and_wrong_return_layout_withhold_arguments(self):
        self.assert_withheld(self.evaluate(types=['string']))
        call = copy.deepcopy(self.call)
        call['outcome'] = {'error': {'code': 3, 'message': 'execution reverted'}}
        self.assert_withheld(self.evaluate(call))

    def test_corrupted_proof_and_wrong_anchor_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle['observation']['nodes'][0]['code_hash'] = '0x' + 'ab' * 32
        with self.assertRaises(ValueError):
            tool.evaluate(bundle, self.call, 'balanceOf(address)', ['uint256'])
        with self.assertRaises(ValueError):
            tool.evaluate(self.bundle, self.call, 'balanceOf(address)', ['uint256'], '0x' + 'ab' * 32)

    def test_digest_binds_call_context_and_layout(self):
        first = self.evaluate()
        call = copy.deepcopy(self.call)
        call['call']['from'] = tool.context.returns.core.TOKENS['ZTO']
        changed = self.evaluate(call)
        self.assertNotEqual(first['input_sha256']['call_observation'],
                            changed['input_sha256']['call_observation'])
        self.assertEqual(changed['call']['from'], call['call']['from'])
        other_layout = self.evaluate(types=['bytes32'])
        self.assertNotEqual(first['input_sha256']['caller_choices'],
                            other_layout['input_sha256']['caller_choices'])

    def test_cli_offline_success_and_invalid_combination(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(tool.context.returns.core, 'RPC', side_effect=AssertionError('no network')):
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(tool.main(['--demo']), 0)
                self.assertEqual(tool.main(['--demo', '--signature', 'balanceOf(address)']), 1)
        self.assertEqual(json.loads(out.getvalue())['verdict'], 'aligned')
        self.assertEqual(json.loads(err.getvalue())['verdict'], 'invalid')

    def test_cli_mismatch_withholds_both_and_exits_two(self):
        scratch = Path('test/scratch').resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        call = copy.deepcopy(self.call)
        call['call']['data'] += '00' * 32
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            path = Path(folder) / 'mutation.json'
            path.write_text(json.dumps(call))
            out = io.StringIO()
            with redirect_stdout(out):
                status = tool.main(['--bundle', str(tool.HERE / 'zto-proof.json'),
                    '--observation', str(path), '--signature', 'balanceOf(address)', '--types', 'uint256'])
            self.assertEqual(status, 2)
            self.assert_withheld(json.loads(out.getvalue()))

    def test_copy_is_exact_line_source(self):
        self.assertEqual((tool.HERE / 'calldata-lens/calldata_lens.py').read_bytes(),
                         Path('line-4/tools/calldata-lens/calldata_lens.py').read_bytes())


if __name__ == '__main__':
    unittest.main()
