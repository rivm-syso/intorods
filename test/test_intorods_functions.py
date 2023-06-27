import os
import sys

import pytest

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from intorods.intorods import formattime, parse_extra_options


@pytest.mark.parametrize("ts, output",[(1,' 0 days  0: 0: 1 '),(1000,' 0 days  0:16:40 '),(100000,' 1 days  3:46:40 '),(10000000,'115 days 17:46:40 ')])
def test_formattime(ts, output):
    result = formattime(ts)
    assert result == output

def test_parse_extra_options():
    result = parse_extra_options('option1=value1,option2=value2')
    assert result == { 'option1': 'value1', 'option2': 'value2'}

