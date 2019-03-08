from __future__ import absolute_import, unicode_literals

import threading
import unittest

from ..utils import dedent_ftl

from fluent.runtime import FluentBundle

from unittest.mock import patch
import time


class TestThreadSafety(unittest.TestCase):
    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            foo-bar = { foo } Bar
        """))

    def test_is_dirty_isolation(self):
        count = 0
        all_errs = []

        from fluent.runtime.resolver import resolve as original_resolve

        def new_resolve(fluentish, env):
            time.sleep(0.1)
            return original_resolve(fluentish, env)

        def run():
            val, errs = self.ctx.format('foo-bar', {})
            all_errs.extend(errs)

        with patch('fluent.runtime.resolver.resolve', new=new_resolve):
            while count < 20 and len(all_errs) == 0:
                count += 1
                threads = []

                for i in range(0, 100):
                    threads.append(threading.Thread(target=run))

                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

        if all_errs:
            self.fail(all_errs[0])
