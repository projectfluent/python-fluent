import argparse
import os
import json
import hglib
from hglib.util import b, cmdbuilder
from compare_locales.parser import getParser


class Blame(object):
    def __init__(self, repopath):
        self.client = hglib.open(repopath)
        self.users = []
        self.blame = {}

    def main(self):
        for manifestline in self.client.manifest():
            leaf = manifestline[-1]
            self.handleFile(leaf)
        return {'authors': self.users,
                'blame': self.blame}

    def handleFile(self, leaf):
        try:
            parser = getParser(leaf)
        except UserWarning:
            return
        args = cmdbuilder(b('annotate'), d=True, u=True, T='json',
                          *['path:' + leaf])
        blame_json = ''.join(self.client.rawcommand(args))
        blames = json.loads(blame_json)
        fname = os.path.join(self.client.root(), leaf)
        parser.readFile(fname)
        entities, emap = parser.parse()
        self.blame[leaf] = {}
        for e in entities:
            blines = blames[(e.value_position()[0] - 1):e.value_position(-1)[0]]
            blines.sort(key=lambda blame: -blame['date'][0])  # ignore timezone
            blame = blines[0]
            user = blame['user']
            timestamp = blame['date'][0]  # ignore timezone
            if user not in self.users:
                self.users.append(user)
            userid = self.users.index(user)
            self.blame[leaf][e.key] = [userid, timestamp]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("repopath")
    args = parser.parse_args()
    blame = Blame(args.repopath)
    blimey = blame.main()
    print(json.dumps(blimey, indent=4, separators=(',', ': ')))
