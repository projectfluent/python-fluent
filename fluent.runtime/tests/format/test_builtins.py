from datetime import date, datetime
from decimal import Decimal

import pytest

from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentReferenceError
from fluent.runtime.types import fluent_date, fluent_number

from ..utils import dedent_ftl


class TestNumberBuiltin:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    implicit-call    = { 123456 }
                    implicit-call2   = { $arg }
                    defaults         = { NUMBER(123456) }
                    percent-style    = { NUMBER(1.234, style: "percent") }
                    currency-style   = { NUMBER(123456, style: "currency", currency: "USD") }
                    from-arg         = { NUMBER($arg) }
                    merge-params     = { NUMBER($arg, useGrouping: 0) }
                    """
                )
            )
        )
        return bundle

    def test_implicit_call(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("implicit-call").value, {})
        assert val == "123,456"
        assert len(errs) == 0

    def test_implicit_call2_int(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("implicit-call2").value, {"arg": 123456}
        )
        assert val == "123,456"
        assert len(errs) == 0

    def test_implicit_call2_float(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("implicit-call2").value, {"arg": 123456.0}
        )
        assert val == "123,456"
        assert len(errs) == 0

    def test_implicit_call2_decimal(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("implicit-call2").value,
            {"arg": Decimal("123456.0")},
        )
        assert val == "123,456"
        assert len(errs) == 0

    def test_defaults(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("defaults").value, {})
        assert val == "123,456"
        assert len(errs) == 0

    def test_percent_style(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("percent-style").value, {})
        assert val == "123%"
        assert len(errs) == 0

    def test_currency_style(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("currency-style").value, {}
        )
        assert val == "$123,456.00"
        assert len(errs) == 0

    def test_from_arg_int(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("from-arg").value, {"arg": 123456}
        )
        assert val == "123,456"
        assert len(errs) == 0

    def test_from_arg_float(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("from-arg").value, {"arg": 123456.0}
        )
        assert val == "123,456"
        assert len(errs) == 0

    def test_from_arg_decimal(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("from-arg").value, {"arg": Decimal("123456.0")}
        )
        assert val == "123,456"
        assert len(errs) == 0

    def test_from_arg_missing(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("from-arg").value, {})
        assert val == "arg"
        assert len(errs) == 1
        assert errs == [FluentReferenceError("Unknown external: arg")]

    def test_partial_application(self, bundle):
        number = fluent_number(123456.78, currency="USD", style="currency")
        val, errs = bundle.format_pattern(
            bundle.get_message("from-arg").value, {"arg": number}
        )
        assert val == "$123,456.78"
        assert len(errs) == 0

    def test_merge_params(self, bundle):
        number = fluent_number(123456.78, currency="USD", style="currency")
        val, errs = bundle.format_pattern(
            bundle.get_message("merge-params").value, {"arg": number}
        )
        assert val == "$123456.78"
        assert len(errs) == 0


class TestDatetimeBuiltin:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    implicit-call = { $date }
                    explicit-call = { DATETIME($date) }
                    call-with-arg = { DATETIME($date, dateStyle: "long") }
                    """
                )
            )
        )
        return bundle

    def test_implicit_call_date(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("implicit-call").value, {"date": date(2018, 2, 1)}
        )
        assert val == "Feb 1, 2018"
        assert len(errs) == 0

    def test_implicit_call_datetime(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("implicit-call").value,
            {"date": datetime(2018, 2, 1, 14, 15, 16)},
        )
        assert val == "Feb 1, 2018"
        assert len(errs) == 0

    def test_explicit_call_date(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("explicit-call").value, {"date": date(2018, 2, 1)}
        )
        assert val == "Feb 1, 2018"
        assert len(errs) == 0

    def test_explicit_call_datetime(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("explicit-call").value,
            {"date": datetime(2018, 2, 1, 14, 15, 16)},
        )
        assert val == "Feb 1, 2018"
        assert len(errs) == 0

    def test_explicit_call_date_fluent_date(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("explicit-call").value,
            {"date": fluent_date(date(2018, 2, 1), dateStyle="short")},
        )
        assert val == "2/1/18"
        assert len(errs) == 0

    def test_arg(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("call-with-arg").value, {"date": date(2018, 2, 1)}
        )
        assert val == "February 1, 2018"
        assert len(errs) == 0

    def test_arg_overrides_fluent_date(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("call-with-arg").value,
            {"date": fluent_date(date(2018, 2, 1), dateStyle="short")},
        )
        assert val == "February 1, 2018"
        assert len(errs) == 0
