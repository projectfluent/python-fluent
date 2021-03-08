from datetime import date
import subprocess


def get_tag_infos(cut_off_date):
    '''Get fluent.* tags newer than cut_off_date.
    TagInfo objects are ordered by committer date, newest first.
    '''
    taglines = subprocess.run(
        [
            'git', 'tag', '--list', 'fluent.*',
            '--sort=-committerdate',
            '--format=%(refname:lstrip=2) %(committerdate:short)',
        ],
        encoding='utf-8',
        stdout=subprocess.PIPE,
        check=True
    ).stdout.splitlines()
    return [
        ti for ti in (TagInfo(line) for line in taglines)
        if ti.date > cut_off_date
    ]


class TagInfo:
    def __init__(self, tagline):
        tag, date_string = tagline.split(' ')
        self.project, self.version = tag.split('@')
        self.date = date.fromisoformat(date_string)

    @property
    def tag(self):
        return f'{self.project}@{self.version}'

    def __repr__(self):
        return f'{self.tag} ({self.date})'
