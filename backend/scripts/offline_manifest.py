"""Create/verify a SHA-256 manifest for an operator-staged offline release directory.

This verifies transfer integrity, not publisher authenticity. Keep/sign the manifest
outside the writable bundle. Never point this at live organizational data.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Bundle must not contain symlinks or paths outside its root')
        if path.is_file() and path.name != 'manifest.sha256.json':
            result[path.relative_to(root).as_posix()] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'verify'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    if not root.is_dir(): parser.error('Directory required')
    path = root / 'manifest.sha256.json'
    actual = inventory(root)
    if args.action == 'create':
        if not actual: parser.error('Cannot manifest an empty release')
        # Exclusive create prevents silently blessing changed contents.
        with path.open('x', encoding='utf-8') as file:
            json.dump({'format': 1, 'files': actual}, file, indent=2)
        print(json.dumps({'files': len(actual), 'manifest': str(path)}))
        return 0
    expected = json.loads(path.read_text(encoding='utf-8'))['files']
    changed = sorted(k for k in expected.keys() | actual.keys() if expected.get(k) != actual.get(k))
    print(json.dumps({'valid': not changed, 'changed_missing_or_extra': changed}))
    return 1 if changed else 0


if __name__ == '__main__':
    raise SystemExit(main())
