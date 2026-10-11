from photo_importer.application.cancellation_token import CancellationToken


def test_not_cancelled_initially():
    assert CancellationToken().is_cancel_requested is False


def test_request_cancel_sets_flag():
    token = CancellationToken()

    token.request_cancel()

    assert token.is_cancel_requested is True


def test_request_cancel_is_idempotent():
    token = CancellationToken()

    token.request_cancel()
    token.request_cancel()

    assert token.is_cancel_requested is True
