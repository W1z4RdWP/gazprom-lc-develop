document.addEventListener('DOMContentLoaded', function() {
    // Обработка раскрытия списка уроков
    document.querySelectorAll('.lessons-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const icon = this.querySelector('i');
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            if (isExpanded) {
                icon.classList.remove('bi-chevron-up');
                icon.classList.add('bi-chevron-down');
            } else {
                icon.classList.remove('bi-chevron-down');
                icon.classList.add('bi-chevron-up');
            }
        });
    });
});

// Функции для inline редактирования названия категории
function editDirectoryName(directoryId) {
    const container = document.querySelector(`.item-name-container[data-directory-id="${directoryId}"]`);
    if (!container) return;
    
    const display = container.querySelector('.item-name-display');
    const form = container.querySelector('.edit-name-form');
    const input = form.querySelector('input');
    
    if (display && form) {
        display.style.display = 'none';
        form.style.display = 'inline-block';
        input.focus();
        input.select();
    }
}

function cancelEditDirectoryName(directoryId, showConfirm = true) {
    const container = document.querySelector(`.item-name-container[data-directory-id="${directoryId}"]`);
    if (!container) return;
    
    const display = container.querySelector('.item-name-display');
    const form = container.querySelector('.edit-name-form');
    const input = form.querySelector('input');
    
    if (display && form) {
        // Проверяем, изменилось ли значение
        const originalValue = display.textContent.trim();
        const currentValue = input.value.trim();
        
        if (showConfirm && originalValue !== currentValue) {
            if (!confirm('Отменить редактирование?')) {
                return; // Пользователь не подтвердил отмену
            }
        }
        
        // Восстанавливаем исходное значение
        input.value = originalValue;
        form.style.display = 'none';
        display.style.display = 'inline';
    }
}

function saveDirectoryName(directoryId) {
    const container = document.querySelector(`.item-name-container[data-directory-id="${directoryId}"]`);
    if (!container) return;
    
    const form = container.querySelector('.edit-name-form');
    const input = form.querySelector('input');
    const display = container.querySelector('.item-name-display');
    const newName = input.value.trim();
    
    if (!newName) {
        alert('Название не может быть пустым');
        input.focus();
        return;
    }
    
    // Отправляем AJAX запрос
    fetch(`/kb/directory/${directoryId}/edit-name/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ name: newName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            display.textContent = data.name;
            form.style.display = 'none';
            display.style.display = 'inline';
        } else {
            alert('Ошибка: ' + (data.error || 'Не удалось сохранить изменения'));
            input.focus();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при сохранении');
        input.focus();
    });
}

// Функция для получения CSRF токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Обработка нажатия Enter и Escape в поле ввода, а также клика вне области редактирования
document.addEventListener('DOMContentLoaded', function() {
    // Используем делегирование событий для динамически создаваемых элементов
    document.addEventListener('keypress', function(e) {
        if (e.target.classList.contains('directory-name-input')) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const directoryId = parseInt(e.target.getAttribute('data-directory-id'));
                saveDirectoryName(directoryId);
            }
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.target.classList.contains('directory-name-input')) {
            if (e.key === 'Escape') {
                e.preventDefault();
                const directoryId = parseInt(e.target.getAttribute('data-directory-id'));
                cancelEditDirectoryName(directoryId);
            }
        }
    });
    
    // Обработка клика вне области редактирования
    document.addEventListener('click', function(e) {
        // Проверяем, есть ли активное редактирование
        const activeForm = document.querySelector('.edit-name-form[style*="inline"]');
        if (!activeForm) return;
        
        const clickedElement = e.target;
        
        // Проверяем, что клик был не по форме редактирования и не по кнопке редактирования
        const isClickInsideForm = activeForm.contains(clickedElement);
        const isClickOnEditButton = clickedElement.closest('.edit-directory-btn');
        const isClickOnSaveButton = clickedElement.closest('.btn-success');
        
        // Если клик был внутри формы или по кнопке редактирования/сохранения, ничего не делаем
        if (isClickInsideForm || isClickOnEditButton || isClickOnSaveButton) {
            return;
        }
        
        // Клик был вне области редактирования - отменяем редактирование с подтверждением
        const directoryId = parseInt(activeForm.querySelector('input').getAttribute('data-directory-id'));
        cancelEditDirectoryName(directoryId);
    });
});