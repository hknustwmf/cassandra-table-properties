# pylint: disable=missing-docstring, broad-except, invalid-name, no-self-use
import datetime
import os

import table_properties.utils as util


def get_temp_filename(prefix: str):
    return prefix + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


class TestFindByValue():
    def test_simple_list(self):
        l = [1, 2, 3, 4]
        assert util.find_by_value(l, "a", 1) is None

    def test_nonnested_dict_list(self):
        l = [{"a": 1, "b": 2}, {"c": 3, "d": 4}, {}, {"e": 1}]
        assert isinstance(util.find_by_value(l, "a", 1), dict)
        assert util.find_by_value(l, "a", 1) == {"a": 1, "b": 2}
        assert util.find_by_value(l, "f", 99) is None
        assert util.find_by_value(l, "d", 4) == {"c": 3, "d": 4}
        assert util.find_by_value(l, "e", 1) == {"e": 1}
        assert util.find_by_value(l, "e", None) is None


class TestInputOutput():
    def test_read_yaml_config(self):
        orig = util.load_yaml("./tests/configs/excalibur_unchanged.yaml")
        assert orig is not None

    def test_app_path(self):
        assert util.get_app_folder() == os.path.abspath(".")
