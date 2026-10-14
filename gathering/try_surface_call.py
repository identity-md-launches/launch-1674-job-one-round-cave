#!/usr/bin/env python3
"""Read ZTO balanceOf(PoolManager) at the saved proof block; never send a transaction."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
POOL_MANAGER = '0x000000000004444c5dc75cb358380d2e3de08a90'


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--one':
        sys.path.insert(0, str(ROOT / 'shared/surface-return'))
        import surface_call as tool
        bundle, _ = tool.context.demo_inputs()
        signature = 'balanceOf(address)'
        data = tool.context.surface.signature_selector(signature) + POOL_MANAGER[2:].rjust(64, '0')
        # The real PoolManager asks for its own balance in eth_call only. This
        # explicit simulation context neither claims control nor needs a wallet.
        call = {'to': bundle['observation']['target'], 'from': POOL_MANAGER,
                'data': data, 'value': '0x0'}
        changes = tool.context.returns.changes
        obs = changes.capture(changes.core.RPC(sys.argv[2]), call, 'uint256',
                              bundle['observation']['block']['number'])
        result = tool.evaluate(bundle, obs, signature, ['uint256'])
        changes.save_observation(ROOT / 'gathering/zto-pool-balance-call.json', obs)
        (ROOT / 'gathering/zto-pool-balance-context.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({'verdict': result['verdict'], 'block': obs['block'],
                          'arguments': result['decoded_arguments'], 'values': result['decoded_values']}))
        return 0 if result['verdict'] == 'aligned' else 2
    attempts = []
    for endpoint in ('https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org'):
        try:
            done = subprocess.run([sys.executable, '-B', __file__, '--one', endpoint],
                                  capture_output=True, text=True, timeout=45)
            attempts.append({'endpoint': endpoint, 'exit': done.returncode,
                             'stdout': done.stdout, 'stderr': done.stderr[-3000:]})
            if done.returncode == 0:
                break
        except subprocess.TimeoutExpired:
            attempts.append({'endpoint': endpoint, 'error': '45-second process deadline exceeded'})
    result = {'read_only': True, 'attempts': attempts,
              'aligned': any(a.get('exit') == 0 for a in attempts)}
    (ROOT / 'gathering/surface-call-live-attempts.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return 0 if result['aligned'] else 2


if __name__ == '__main__':
    sys.exit(main())
