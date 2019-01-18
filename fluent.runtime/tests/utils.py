from __future__ import unicode_literals

import textwrap


def dedent_ftl(text):
    return textwrap.dedent("{}\n".format(text.rstrip()))
