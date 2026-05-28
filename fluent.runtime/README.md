# fluent.runtime

Use [Fluent](https://projectfluent.org/) to localize your Python application.
It comes with a `Localization` class to use, based on an implementation of `FluentBundle`.
It uses the parser from `fluent.syntax` to read Fluent files.

```python
from datetime import date
l10n = DemoLocalization("today-is = Today is { $today }")
val = l10n.format_value("today-is", { "today": date.today() })
val # 'Today is Jun 16, 2018'
```

Find the full documentation at https://projectfluent.org/python-fluent/fluent.runtime/.
