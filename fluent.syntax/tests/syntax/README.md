The files in `fixtures_*` are copied from `fluent.js/fluent-syntax`. Due to
the backwards compatibility with Syntax 0.4, the Python parser sometimes
produces different output, mainly in terms of reported errors. Currently, the
files which are known to differ are:

    fixtures_behavior/standalone_identifier.ftl
    fixtures_structure/multiline_pattern.ftl
