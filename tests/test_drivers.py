import pytest
import sqlite3

import db


class DriverTests(object):

    def clear_drivers(self):
        db.drivers._DRIVERS = {}

    def make_driver(self, label):

        class TestDriver(db.drivers.Driver):

            def __init__(self, *args, **kwargs):
                super(TestDriver, self).__init__(*args, **kwargs)
                self.driver_label = label
                self.invocations = []

            def connect(self, *args, **kwargs):
                invocation = (label, args, kwargs)
                self.invocations.append(invocation)
                return invocation

        driver = TestDriver()
        return driver

    def install_one_driver(self):
        db.drivers.clear()
        self.only_db = \
            db.drivers.register(self.make_driver("connect_one_only"), "only")

    def install_one_default_driver(self):
        db.drivers.clear()
        self.default_db = \
            db.drivers.register(self.make_driver("connect_default_only"))

    def install_two_drivers(self):
        db.drivers.clear()
        self.first_db = \
            db.drivers.register(
                self.make_driver("connect_two_first"), "first")
        self.second_db = \
            db.drivers.register(
                self.make_driver("connect_two_second"), "second")


class TestCount(DriverTests):

    def test_none(self):
        self.clear_drivers()
        assert db.drivers.count() == 0

    def test_one(self):
        self.install_one_driver()
        assert db.drivers.count() == 1

    def test_two(self):
        self.install_two_drivers()
        assert db.drivers.count() == 2


class TestClear(DriverTests):

    def test_already_clear(self):
        self.clear_drivers()
        db.drivers.clear()
        assert db.drivers.count() == 0

    def test_not_already_clear(self):
        self.install_one_driver()
        db.drivers.clear()
        assert db.drivers.count() == 0

    def test_not_already_clear_multiple(self):
        self.install_two_drivers()
        db.drivers.clear()
        assert db.drivers.count() == 0


class TestGet(DriverTests):

    def test_default_one_default_driver(self):
        self.install_one_default_driver()
        default_db = db.get()
        assert default_db.driver.driver_label == "connect_default_only"

    def test_default_one_non_default_driver(self):
        self.install_one_driver()
        default_db = db.get()
        with pytest.raises(KeyError):
            db.items("SELECT * FROM foo")

    def test_named_one_named_driver(self):
        self.install_one_driver()
        named_db = db.get("only")
        assert named_db.driver.driver_label == "connect_one_only"

    def test_each_of_two_named_drivers(self):
        self.install_two_drivers()
        first_db = db.get("first")
        assert first_db.driver.driver_label == "connect_two_first"
        second_db = db.get("second")
        assert second_db.driver.driver_label == "connect_two_second"


class TestMisc(DriverTests):

    def test_registering_returns_db(self):
        test_db = db.drivers.sqlite3x.register(":memory:", "test_db")

        assert test_db is not None

        test_db.do("""CREATE TABLE foo (
            foo_id INTEGER PRIMARY KEY,
            bar TEXT NOT NULL
        )""")
        test_db.do("INSERT INTO foo (foo_id, bar) VALUES (1, 'a')")
        test_db.do("INSERT INTO foo (foo_id, bar) VALUES (2, 'b')")
        test_db.do("INSERT INTO foo (foo_id, bar) VALUES (3, 'c')")

        assert test_db.item("SELECT COUNT(*) AS n FROM foo").n == 3
