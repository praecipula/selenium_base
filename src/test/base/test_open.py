import pytest
import uri_open

@pytest.fixture
def open_command():
    return uri_open.Open(["https://www.example.com"])

def test_returns_true_on_success(open_command):
    assert open_command.execute() == True
