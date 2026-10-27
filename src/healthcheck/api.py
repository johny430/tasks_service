from fastapi import APIRouter

router = APIRouter(tags=['Healthcheck'])


@router.get('/healthcheck', summary='Проверка, что сервис запущен')
async def get_healthcheck() -> dict[str, str]:
    return {'status': 'ok'}
