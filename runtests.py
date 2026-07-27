#!/usr/bin/env python3
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

from django import setup
from django.test.utils import get_runner
from django.conf import settings


def main():
    setup()
    test_runner = get_runner(settings)(verbosity=2)
    failures = test_runner.run_tests(["tests"])
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()

