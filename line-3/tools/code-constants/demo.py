"""Offline real ZTO-first proof replay; no network or invented trust anchor."""
import json
from pathlib import Path
import code_constants as constants

FOLDER = Path(__file__).resolve().parent


def main():
    results = []
    for token in ('zto', 'imd'):
        bundle = constants.ancestry.read_json(FOLDER.parent / 'code-delta' / (token + '-later-proof.json'))
        result = constants.inspect(bundle)
        results.append({'token': token.upper(), 'target': result['target'],
                        'code_block': result['code_block'], 'anchor': result['proof']['anchor'],
                        'runtimes': result['runtimes'], 'dependencies_verified': result['dependencies_verified']})
    return {'demonstration_passed': all(r['anchor'] == 'unanchored-rpc-header'
                                       and not r['dependencies_verified'] for r in results),
            'results': results, 'scope': 'Real historical code proof replay; literal syntax only.'}


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['demonstration_passed'] else 1)
