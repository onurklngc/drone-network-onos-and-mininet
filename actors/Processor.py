import settings as s


class CloudProcessor(object):
    process_speed = s.CLOUD_PROCESSOR_SPEED
    all_processed_tasks = None
    currently_processed_tasks = None
    next_complete_event_time = None

    def __init__(self):
        self.currently_processed_tasks = []
        self.all_processed_tasks = []
