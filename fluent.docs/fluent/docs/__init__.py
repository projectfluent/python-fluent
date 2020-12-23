from pathlib import Path

from .build import build


__all__ = [
    'build',
    'pre_pub',
]


def pre_pub(repo_name):
    """Prepare staging area for publishing on Github pages."""
    root = Path('_build') / repo_name
    # Ensure `.nojekyll`
    with open(root / '.nojekyll', 'w') as fh:
        fh.write('')
    # Remove static files from subprojects, but leave
    # `documentation_options.js` alone. That's per project, probably.
    # We built to root/fluent.*/stable, so glob that.
    for staticfile in root.glob('fluent.*/stable/_static/*'):
        if staticfile.name != 'documentation_options.js':
            staticfile.unlink()
