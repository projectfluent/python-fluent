``fluent.docs``
===============

Python utilities used by the ``python-fluent`` documentation build
process. The entry point is ``scripts/build-docs``.

The generated documentation is in ``_build/python-fluent``, and you
can surf it locally via ``python3 -m http.server `` in ``_build``.

The documentation is created for each tagged version after May 2020,
at which point we had good docs. The current branch (PR tips or
master) is versioned as *dev*, and *stable* is a symlink to the latest
release. The releases are in a dir with their corresponding version number.

When cutting a new release, manually run the documentation workflow
to pick that up.

The rationale for regenerating all historic documentation releases is
to provide an easy process to change style and renderering across
the full documentation. For that, the build setup is taken from
the current checkout, and release docs are generated from sources in
a git worktree.
