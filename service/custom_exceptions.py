class PortfolioException(Exception):
    def __init__(self, source: str, message: str):
        self.source = source
        super().__init__(message)
