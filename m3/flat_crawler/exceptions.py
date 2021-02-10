
class CrawlingException(Exception):
    pass


class URLFailedToLoadException(CrawlingException):
    pass


class PostHeadingMissing(CrawlingException):
    pass


class PostURLMissing(CrawlingException):
    pass


class PostFailedToSave(CrawlingException):
    pass