class DownloadException(Exception):
    """Raised when an error occurs during downloading."""
    def __init__(self, message="An error occurred during downloading"):
        self.message = message
        super().__init__(self.message)

class UploadException(Exception):
    """Raised when an error occurs during uploading."""
    def __init__(self, message="An error occurred during upload"):
        self.message = message
        super().__init__(self.message)

class SyncException(Exception):
    """Raised when an error occurs during syncing."""
    def __init__(self, message="An error occurred during syncing"):
        self.message = message
        super().__init__(self.message)

class FolderManagementException(Exception):
    """Raised when an error occurs during syncing."""
    def __init__(self, message="An error occurred during Folder management"):
        self.message = message
        super().__init__(self.message)

class LicenseException(Exception):
    """Raised when an error occurs during license validation."""
    def __init__(self, message="An error occurred during license validation"):
        self.message = message
        super().__init__(self.message)

class GoogleServiceException(Exception):
    """Raised when an error occurs during google service creation."""
    def __init__(self, message="An error occurred during google service creation"):
        self.message = message
        super().__init__(self.message)

