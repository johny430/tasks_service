import enum


class TaskStatusEnum(enum.StrEnum):
    """Статусы задачи"""

    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    CANCELLED = 'cancelled'
