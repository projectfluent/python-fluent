import textwrap


def dedent_ftl(text):
    return textwrap.dedent(f"{text.rstrip()}\n")
