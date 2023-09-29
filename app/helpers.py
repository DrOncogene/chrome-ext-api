from app.settings import settings


def generate_link(collection: str, file_id: str) -> str:
    """generates a link to a video"""

    return f'{settings.SERVER_URL}/videos/{collection}/{file_id}'
