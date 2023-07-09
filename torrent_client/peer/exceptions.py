class PeerReturnInvalidResponseError(Exception):
    pass


class PeerUnexpectedBehaviorError(Exception):
    pass


class PeerNotRespondingError(Exception):
    pass


class NoPieceNeededError(Exception):
    pass


class ChokedWhileRequestingError(Exception):
    pass


class CorruptedPieceError(Exception):
    pass


class PeerTimeOutError(Exception):
    pass
