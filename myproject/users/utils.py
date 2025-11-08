import os, uuid

def get_profile_image_path(instance, filename):
    """
    Генерирует путь для сохранения изображения профиля.
    Автоматически переименовывает файл, чтобы избежать проблем с кириллицей.
    
    Args:
        instance: Экземпляр модели Profile
        filename: Исходное имя файла
        
    Returns:
        str: Путь для сохранения файла
    """
    # Получаем расширение файла
    ext = filename.split('.')[-1]
    # Генерируем уникальное имя файла на основе username и UUID
    filename = f"{instance.user.username}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('profile_pics', filename)