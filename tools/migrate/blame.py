import argparse
import json
from os.path import join

from compare_locales.parser import getParser, Junk
import hglib
from hglib.util import b, cmdbuilder


class Blame(object):
    def __init__(self, repopath):
        self.client = hglib.open(repopath)
        self.users = []
        self.blame = {}

    def main(self, file_paths):
        args = cmdbuilder(
            b('annotate'), template='json', date=True, user=True,
            cwd=self.client.root(), file=map(b, file_paths))
        blame_json = ''.join(self.client.rawcommand(args))
        file_blames = json.loads(blame_json)

        for file_blame in file_blames:
            self.handleFile(file_blame)

        return {'authors': self.users,
                'blame': self.blame}

    def handleFile(self, file_blame):
        path = file_blame['path']

        try:
            parser = getParser(path)
        except UserWarning:
            return

        self.blame[path] = {}

        parser.readFile(join(self.client.root(), path))
        entities, emap = parser.parse()
        for e in entities:
            if isinstance(e, Junk):
                continue
            entity_lines = file_blame['lines'][
                (e.value_position()[0] - 1):e.value_position(-1)[0]
            ]
            # ignore timezone
            entity_lines.sort(key=lambda blame: -blame['date'][0])
            line_blame = entity_lines[0]
            user = line_blame['user']
            timestamp = line_blame['date'][0]  # ignore timezone
            if user not in self.users:
                self.users.append(user)
            userid = self.users.index(user)
            self.blame[path][e.key] = [userid, timestamp]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('repo_path')
    parser.add_argument('file_path', nargs='+')
    args = parser.parse_args()
    blame = Blame(args.repo_path)
    blimey = blame.main(args.file_path)
    print(json.dumps(blimey, indent=4, separators=(',', ': ')))
