from configparser import ConfigParser
import os
from pathlib import Path
import subprocess


def get_version(root):
    if root == '.':
        return
    cp = ConfigParser()
    cp.read(Path(root) / 'setup.cfg')
    return cp.get('metadata', 'version')


def build(repo_name, doc_roots):
    for doc_root in doc_roots:
        env = os.environ.copy()
        version = get_version(doc_root)
        cmd = [
            'sphinx-build',
            '-c', 'docs',
            '-a', '-E', '-W',
            '-A', 'root_url=/' + repo_name,
            '-d', '_build/doctrees/' + doc_root,
        ]
        if version:
            env['PYTHONPATH'] = doc_root
            cmd += [
                '-D', 'release=' + version,
                '-D', 'project=' + doc_root,
            ]
            build_dir = '_build/' + repo_name + '/' + doc_root + '/stable'
        else:
            build_dir = '_build/' + repo_name
        cmd += [
            doc_root + '/docs',
            build_dir,
        ]
        subprocess.check_call(' '.join(cmd), env=env, shell=True)
        if build_dir.endswith('/stable'):
            with open(build_dir.replace('/stable', '/index.html'), 'w') as index:
                index.write('<meta http-equiv="refresh" content="0; URL=stable/">\n')
