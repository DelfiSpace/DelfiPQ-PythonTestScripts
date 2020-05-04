# ADCS-specific test cases
import pytest
import sys
sys.path.insert(1, '../Generic')

import PQ9Client
import time
import json

def test_ADCS(pq9_connection, destination):
    print("ADCS specific tests")
