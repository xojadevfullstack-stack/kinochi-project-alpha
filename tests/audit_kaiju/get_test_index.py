import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

import pytest

class Collector:
    def __init__(self):
        self.collected = []
    def pytest_collection_modifyitems(self, items):
        self.collected.extend([i.nodeid for i in items])

c = Collector()
pytest.main(['backend/tests/', '--collect-only', '-q'], plugins=[c])
print(f"Total collected: {len(c.collected)}")
for i in range(85, min(95, len(c.collected))):
    print(f"Index {i}: {c.collected[i]}")
