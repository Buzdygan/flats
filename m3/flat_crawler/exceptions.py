
class CrawlingException(Exception):
    pass


class URLFailedToLoadException(CrawlingException):
    pass


class PostHeadingMissing(CrawlingException):
    pass


class PostURLMissing(CrawlingException):
    pass

class PostDTPostedMissing(CrawlingException):
    pass


class PostFailedToSave(CrawlingException):
    pass


class NotRecognizedDistrict(Exception):
    pass


class InvalidTimedeltaStr(CrawlingException):
    pass