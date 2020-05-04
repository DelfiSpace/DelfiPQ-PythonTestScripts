import os, pathlib
import pytest

# test to run module-specific tests from 'root' folder using a target string.
if __name__ == "__main__":
    target = 'EPS'
    os.chdir(target)
    pytest.main()