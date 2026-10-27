import typing as t

from fastapi import APIRouter, HTTPException, Path, status

from src.core.constants import MAX_BIGINT
from src.core.database.di import SessionDep
from src.core.schemas import ErrorResponseSchema
from src.tasks.dtos import TaskDTO
from src.tasks.exceptions import TaskNotFoundError
from src.tasks.logic.use_cases import DeleteTaskUseCase, UpdateTaskStatusUseCase
from src.tasks.schemas import OkResponseSchema, TaskSchema, TaskStatusUpdateSchema

tasks_router = APIRouter(prefix='/tasks', tags=['Tasks'])

TaskIdPath = t.Annotated[int, Path(description='ID задачи', ge=1, le=MAX_BIGINT)]

TASK_NOT_FOUND_RESPONSES: dict[int | str, dict[str, t.Any]] = {
    status.HTTP_404_NOT_FOUND: {'model': ErrorResponseSchema, 'description': 'Задача не найдена'},
}


def _task_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Задача не найдена')


@tasks_router.patch(
    '/{task_id}/status',
    summary='Изменяет статус задачи',
    response_model=TaskSchema,
    responses=TASK_NOT_FOUND_RESPONSES,
)
async def update_task_status(session: SessionDep, task_id: TaskIdPath, status_data: TaskStatusUpdateSchema) -> TaskDTO:
    use_case = UpdateTaskStatusUseCase(session=session, task_id=task_id, status=status_data.status)
    try:
        return await use_case.execute()
    except TaskNotFoundError as err:
        raise _task_not_found() from err


@tasks_router.delete(
    '/{task_id}',
    summary='Удаляет задачу',
    response_model=OkResponseSchema,
    responses=TASK_NOT_FOUND_RESPONSES,
)
async def delete_task(session: SessionDep, task_id: TaskIdPath) -> OkResponseSchema:
    use_case = DeleteTaskUseCase(session=session, task_id=task_id)
    try:
        await use_case.execute()
    except TaskNotFoundError as err:
        raise _task_not_found() from err
    return OkResponseSchema()
