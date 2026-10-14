import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calldata_lens


def word(number):
    return number.to_bytes(32, 'big').hex()


class CalldataLensTests(unittest.TestCase):
    def real(self):
        return json.loads((HERE.parent / 'call-rehearsal' / 'zto-observation.json').read_text())

    def test_real_zto_no_argument_call(self):
        report = calldata_lens.decode_call(self.real(), [])
        self.assertEqual(report['verdict'], 'decoded')
        self.assertEqual(report['selector'], '0x18160ddd')
        self.assertEqual(report['arguments'], [])
        self.assertEqual(report['call']['to'], '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e')

    def test_decodes_explicit_address_and_uint_arguments(self):
        observation = self.real()
        observation['call']['from'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        observation['call']['data'] = ('0xa9059cbb' + '0' * 24 + '12' * 20 + word(42))
        report = calldata_lens.decode_call(observation, ['address', 'uint256'])
        self.assertEqual(report['arguments'], [
            {'type': 'address', 'value': '0x' + '12' * 20},
            {'type': 'uint256', 'value': '42'},
        ])

    def test_types_are_not_inferred(self):
        observation = self.real()
        observation['call']['from'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        observation['call']['data'] = '0xa9059cbb' + word(1)
        report = calldata_lens.decode_call(observation, ['uint256'])
        self.assertEqual(report['selector'], '0xa9059cbb')
        self.assertEqual(report['arguments'][0]['value'], '1')

    def test_rejects_missing_selector(self):
        observation = self.real()
        observation['call']['from'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        observation['call']['data'] = '0x'
        with self.assertRaisesRegex(ValueError, 'four-byte selector'):
            calldata_lens.decode_call(observation, [])

    def test_rejects_noncanonical_argument_tail(self):
        observation = self.real()
        observation['call']['from'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        observation['call']['data'] = '0x12345678' + word(1) + word(2)
        with self.assertRaisesRegex(ValueError, 'extra trailing'):
            calldata_lens.decode_call(observation, ['uint256'])

    def test_rejects_empty_type_between_commas(self):
        with self.assertRaisesRegex(ValueError, 'ABI type'):
            calldata_lens.types_argument('address,,uint256')

    def test_cli_demo_is_offline_and_decoded(self):
        run = subprocess.run([sys.executable, '-B', str(HERE / 'calldata_lens.py'), 'demo'],
                             text=True, capture_output=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['selector'], '0x18160ddd')


if __name__ == '__main__':
    unittest.main()
