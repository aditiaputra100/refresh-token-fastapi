import pytest

def test_sample():
    assert 1 + 1 == 2


class TestSample:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup
        print("\nSetup for TestSample")

        yield

        # Teardown
        print("\nTeardown for TestSample")

    def test_sample_method(self):
        assert 2 * 2 == 4

