import textwrap


def dedent_ftl(text):
    return textwrap.dedent("{}\n".format(text.rstrip()))
