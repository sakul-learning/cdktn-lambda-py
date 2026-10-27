from lambda_src.index import handler


def test_handler_returns_hello_world():
    assert handler({}, None) == "hello world"
