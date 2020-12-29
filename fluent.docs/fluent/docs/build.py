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
        version = get_version(doc_root)
        src_dir = doc_root
        project = doc_root
        version = get_version(project)
        builder = ProjectBuilder(repo_name, src_dir, project,  version)
        with builder:
            builder.build()
    for project in doc_roots:
        with open(f'_build/{repo_name}/{project}/index.html', 'w') as index:
            index.write('<meta http-equiv="refresh" content="0; URL=stable/">\n')


class DocBuilder:
    '''Builder for the top-level documentation.
    '''
    build_dir = '_build/doctrees'

    def __init__(self, repo_name, src_dir):
        self.repo_name = repo_name
        self.src_dir = src_dir

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def build(self):
        cmd = self.command()
        env = self.environ()
        subprocess.check_call(cmd, env=env)

    def command(self):
        return self.cmd_prefix + self.cmd_opts + [
            f'{self.src_dir}/docs',
            self.dest_dir,
        ]

    def environ(self):
        return os.environ.copy()

    @property
    def cmd_prefix(self):
        return [
            'sphinx-build',
            '-c', 'docs',
            '-a', '-E', '-W',
            '-A', 'root_url=/' + self.repo_name,
            '-d', self.doc_tree,
        ]

    @property
    def cmd_opts(self):
        return []

    @property
    def dest_dir(self):
        return f'_build/{self.repo_name}'

    @property
    def doc_tree(self):
        return '_build/doctrees'


class ProjectBuilder(DocBuilder):
    '''Builder for individual projects, with project name and version.
    '''
    def __init__(self, repo_name, src_dir, project_name, version):
        super().__init__(repo_name, src_dir)
        self.project_name = project_name
        self.version = version

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove static theme files from project static, they're
        # used from the top-level _static.
        for staticfile in Path(self.dest_dir).glob('_static/*'):
            # The options are project-specific.
            if staticfile.name != 'documentation_options.js':
                staticfile.unlink()

    def environ(self):
        env = super().environ()
        env['PYTHONPATH'] = self.src_dir
        return env

    @property
    def cmd_opts(self):
        return [
                '-D', 'release=' + self.version,
                '-D', 'project=' + self.project_name,
            ]

    @property
    def dest_dir(self):
        return f'_build/{self.repo_name}/{self.project_name}/stable'
