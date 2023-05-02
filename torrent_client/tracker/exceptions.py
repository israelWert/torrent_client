class TrackerFailedTooManyTimesError(Exception):
    def __init__(self, failures,):
        message = f"the trucker has failed {failures}"
        self.failures = failures
        super().__init__(message)


class TrackerNotRespondingError(Exception):
    """ :raise when the tracker protocol find the tracker is not able response"""
    pass


class TrackerNotSportedError(Exception):
    pass


class TrackerCommotionError(Exception):
    """:raise when tracker response with error or unreadable data"""
    pass


class TrackerCommunicationStoppedWarning(Warning):
    """:raise TrackerCommotionError was raised to many times"""
    pass

