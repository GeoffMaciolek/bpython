import os
import tempfile
import unittest

from pathlib import Path
from bpython.importcompletion import ModuleGatherer


class TestSimpleComplete(unittest.TestCase):
    def setUp(self):
        self.module_gatherer = ModuleGatherer()
        self.module_gatherer.modules = [
            "zzabc",
            "zzabd",
            "zzefg",
            "zzabc.e",
            "zzabc.f",
        ]

    def test_simple_completion(self):
        self.assertSetEqual(
            self.module_gatherer.complete(10, "import zza"), {"zzabc", "zzabd"}
        )

    def test_package_completion(self):
        self.assertSetEqual(
            self.module_gatherer.complete(13, "import zzabc."),
            {"zzabc.e", "zzabc.f"},
        )


class TestRealComplete(unittest.TestCase):
    def setUp(self):
        self.module_gatherer = ModuleGatherer()
        while self.module_gatherer.find_coroutine():
            pass
        __import__("sys")
        __import__("os")

    def test_from_attribute(self):
        self.assertSetEqual(
            self.module_gatherer.complete(19, "from sys import arg"), {"argv"}
        )

    def test_from_attr_module(self):
        self.assertSetEqual(
            self.module_gatherer.complete(9, "from os.p"), {"os.path"}
        )

    def test_from_package(self):
        self.assertSetEqual(
            self.module_gatherer.complete(17, "from xml import d"), {"dom"}
        )


class TestAvoidSymbolicLinks(unittest.TestCase):
    def setUp(self):
        with tempfile.TemporaryDirectory() as import_test_folder:
            os.mkdir(os.path.join(import_test_folder, "Level0"))
            os.mkdir(os.path.join(import_test_folder, "Right"))
            os.mkdir(os.path.join(import_test_folder, "Left"))

            current_path = os.path.join(import_test_folder, "Level0")
            Path(os.path.join(current_path, "__init__.py")).touch()

            current_path = os.path.join(current_path, "Level1")
            os.mkdir(current_path)
            Path(os.path.join(current_path, "__init__.py")).touch()

            current_path = os.path.join(current_path, "Level2")
            os.mkdir(current_path)
            Path(os.path.join(current_path, "__init__.py")).touch()

            os.symlink(
                os.path.join(import_test_folder, "Level0", "Level1"),
                os.path.join(current_path, "Level3"),
                True,
            )

            current_path = os.path.join(import_test_folder, "Right")
            Path(os.path.join(current_path, "__init__.py")).touch()

            os.symlink(
                os.path.join(import_test_folder, "Left"),
                os.path.join(current_path, "toLeft"),
                True,
            )

            current_path = os.path.join(import_test_folder, "Left")
            Path(os.path.join(current_path, "__init__.py")).touch()

            os.symlink(
                os.path.join(import_test_folder, "Right"),
                os.path.join(current_path, "toRight"),
                True,
            )

            self.module_gatherer = ModuleGatherer(
                [os.path.abspath(import_test_folder)]
            )
            while self.module_gatherer.find_coroutine():
                pass
            self.filepaths = [
                "Left.toRight.toLeft",
                "Left.toRight",
                "Left",
                "Level0.Level1.Level2.Level3",
                "Level0.Level1.Level2",
                "Level0.Level1",
                "Level0",
                "Right",
                "Right.toLeft",
                "Right.toLeft.toRight",
            ]

    def test_simple_symbolic_link_loop(self):
        for thing in self.module_gatherer.modules:
            self.assertTrue(thing in self.filepaths)
            if thing == "Left.toRight.toLeft":
                self.filepaths.remove("Right.toLeft")
                self.filepaths.remove("Right.toLeft.toRight")
            if thing == "Right.toLeft.toRight":
                self.filepaths.remove("Left.toRight.toLeft")
                self.filepaths.remove("Left.toRight")
            self.filepaths.remove(thing)
        self.assertFalse(self.filepaths)
