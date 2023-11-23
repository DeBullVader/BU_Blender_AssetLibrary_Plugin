class SyncManager:
    current_sync_operator = None

    @classmethod
    def start_sync(cls, operator_name):
        if cls.current_sync_operator is None:
            cls.current_sync_operator = operator_name
            return True
        return False
    
    @classmethod
    def is_sync_operator(cls, operator_name):
        if cls.current_sync_operator == operator_name:
            return True
        return False
    def get_sync_operator(cls):
        return cls.current_sync_operator
    @classmethod
    def finish_sync(cls, operator_name):
        if cls.current_sync_operator == operator_name:
            cls.current_sync_operator = None

    @classmethod
    def is_sync_in_progress(cls):
        return cls.current_sync_operator is not None
