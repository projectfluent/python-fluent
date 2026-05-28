# fluent.syntax

Read, write, and transform [Fluent](https://projectfluent.org/) files.

This package includes the parser, serializer, and traversal
utilities like Visitor and Transformer. You’re looking for this package
if you work on tooling for Fluent in Python.

```python
from fluent.syntax import parse, ast, serialize
resource = parse("a-key = String to localize")
resource.body[0].value.elements[0].value = "Localized string"
serialize(resource)
# 'a-key = Localized string\n'
```

Find the full documentation at https://projectfluent.org/python-fluent/fluent.syntax/.
