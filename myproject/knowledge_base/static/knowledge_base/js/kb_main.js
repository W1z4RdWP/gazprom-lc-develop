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

// Переменная для отслеживания активного создания категории
let isCreatingDirectory = false;

// Функция для inline создания новой категории
function createNewDirectory(parentId) {
    // Проверяем, есть ли уже активное создание
    if (isCreatingDirectory) {
        // Фокусируемся на уже существующем инпуте
        const existingInput = document.querySelector('.new-directory-input');
        if (existingInput) {
            existingInput.focus();
        }
        return;
    }
    
    isCreatingDirectory = true;
    
    // Находим или создаём секцию "Папки"
    let foldersSection = document.querySelector('.content-section h5.section-header .bi-folder-fill');
    let itemsGrid = null;
    
    if (foldersSection) {
        // Секция существует - находим её grid
        itemsGrid = foldersSection.closest('.content-section').querySelector('.items-grid');
    } else {
        // Секция не существует - создаём её
        const folderContent = document.querySelector('.folder-content');
        
        // Удаляем сообщение о пустой папке, если есть
        const emptyFolder = folderContent.querySelector('.empty-folder');
        if (emptyFolder) {
            emptyFolder.style.display = 'none';
        }
        
        // Создаём секцию папок
        const newSection = document.createElement('div');
        newSection.className = 'content-section';
        newSection.id = 'folders-section';
        newSection.innerHTML = `
            <h5 class="section-header">
                <i class="bi bi-folder-fill me-2"></i>Папки
            </h5>
            <div class="items-grid"></div>
        `;
        
        // Вставляем секцию в начало folder-content
        folderContent.insertBefore(newSection, folderContent.firstChild);
        itemsGrid = newSection.querySelector('.items-grid');
    }
    
    // Создаём элемент новой категории
    const newFolderItem = document.createElement('div');
    newFolderItem.className = 'folder-item new-directory-item';
    newFolderItem.setAttribute('data-parent-id', parentId || '');
    newFolderItem.innerHTML = `
        <div class="item-icon">
            <i class="bi bi-folder-fill"></i>
        </div>
        <div class="item-name-container">
            <form class="edit-name-form" style="display: inline-block;" onsubmit="return false;">
                <input type="text" 
                       class="form-control form-control-sm d-inline-block new-directory-input" 
                       placeholder="Название категории"
                       style="width: auto; min-width: 150px;">
                <button type="button" 
                        class="btn btn-sm btn-success ms-1" 
                        onclick="saveNewDirectory()"
                        title="Сохранить">
                    <i class="bi bi-check"></i>
                </button>
            </form>
        </div>
    `;
    
    // Вставляем в начало grid
    itemsGrid.insertBefore(newFolderItem, itemsGrid.firstChild);
    
    // Фокусируемся на инпуте
    const input = newFolderItem.querySelector('.new-directory-input');
    input.focus();
    
    // Добавляем обработчики событий для нового инпута
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveNewDirectory();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelNewDirectory();
        }
    });
    
    input.addEventListener('blur', function(e) {
        // Проверяем, что клик не был по кнопке сохранения
        setTimeout(() => {
            const relatedTarget = e.relatedTarget;
            if (!relatedTarget || !relatedTarget.closest('.new-directory-item')) {
                const inputValue = input.value.trim();
                if (!inputValue) {
                    cancelNewDirectory();
                }
            }
        }, 100);
    });
}

// Функция для сохранения новой категории
function saveNewDirectory() {
    const newDirItem = document.querySelector('.new-directory-item');
    if (!newDirItem) return;
    
    const input = newDirItem.querySelector('.new-directory-input');
    const name = input.value.trim();
    const parentId = newDirItem.getAttribute('data-parent-id') || null;
    
    // Если название пустое - отменяем создание
    if (!name) {
        cancelNewDirectory();
        return;
    }
    
    // Отключаем инпут на время запроса
    input.disabled = true;
    const saveBtn = newDirItem.querySelector('.btn-success');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    // Отправляем запрос на создание
    fetch('/kb/directory/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ 
            name: name, 
            parent_id: parentId 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Заменяем временный элемент на постоянный
            const directoryId = data.id;
            const directoryName = data.name;
            
            newDirItem.className = 'folder-item';
            newDirItem.removeAttribute('data-parent-id');
            newDirItem.onclick = function(event) {
                if (!event.target.closest('.item-actions') && !event.target.closest('.edit-name-form')) {
                    window.location.href = `/kb/directory/${directoryId}/`;
                }
            };
            
            newDirItem.innerHTML = `
                <div class="item-icon">
                    <i class="bi bi-folder-fill"></i>
                </div>
                <div class="item-name-container" data-directory-id="${directoryId}">
                    <span class="item-name-display">${escapeHtml(directoryName)}</span>
                    <form class="edit-name-form" style="display: none;" onsubmit="return false;">
                        <input type="text" 
                               class="form-control form-control-sm d-inline-block directory-name-input" 
                               value="${escapeHtml(directoryName)}" 
                               style="width: auto; min-width: 150px;"
                               data-directory-id="${directoryId}">
                        <button type="button" 
                                class="btn btn-sm btn-success ms-1" 
                                onclick="saveDirectoryName(${directoryId})"
                                title="Сохранить">
                            <i class="bi bi-check"></i>
                        </button>
                    </form>
                </div>
                <div class="item-actions" onclick="event.stopPropagation();">
                    <button type="button"
                            class="btn btn-sm btn-outline-secondary edit-directory-btn" 
                            title="Редактировать название"
                            onclick="editDirectoryName(${directoryId})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button"
                            class="btn btn-sm btn-outline-danger delete-directory-btn" 
                            title="Удалить категорию"
                            onclick="deleteDirectory(${directoryId}, '${escapeHtml(directoryName).replace(/'/g, "\\'")}')">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            `;
            
            isCreatingDirectory = false;
        } else {
            // Показываем ошибку
            alert('Ошибка: ' + (data.error || 'Не удалось создать категорию'));
            input.disabled = false;
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-check"></i>';
            input.focus();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при создании категории');
        input.disabled = false;
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check"></i>';
        input.focus();
    });
}

// Функция для отмены создания категории
function cancelNewDirectory() {
    const newDirItem = document.querySelector('.new-directory-item');
    if (!newDirItem) return;
    
    newDirItem.remove();
    isCreatingDirectory = false;
    
    // Проверяем, осталась ли секция папок пустой
    const foldersSection = document.getElementById('folders-section');
    if (foldersSection) {
        const itemsGrid = foldersSection.querySelector('.items-grid');
        if (itemsGrid && itemsGrid.children.length === 0) {
            foldersSection.remove();
            
            // Проверяем, пуста ли вся папка
            const folderContent = document.querySelector('.folder-content');
            const hasContent = folderContent.querySelector('.content-section');
            if (!hasContent) {
                // Показываем сообщение о пустой папке
                const emptyFolder = folderContent.querySelector('.empty-folder');
                if (emptyFolder) {
                    emptyFolder.style.display = '';
                }
            }
        }
    }
}

// Вспомогательная функция для экранирования HTML (глобальная версия)
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Функция для удаления категории
function deleteDirectory(directoryId, directoryName) {
    // Сначала проверяем, есть ли содержимое
    fetch(`/kb/directory/${directoryId}/delete/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ action: 'check' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.has_content) {
                // Есть вложенное содержимое - показываем модальное окно с выбором
                showDeleteDirectoryModal(directoryId, directoryName);
            } else {
                // Нет содержимого - простое подтверждение
                if (confirm(`Вы уверены, что хотите удалить категорию "${directoryName}"?`)) {
                    performDeleteDirectory(directoryId, 'delete_all');
                }
            }
        } else {
            alert('Ошибка: ' + (data.error || 'Не удалось проверить категорию'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при проверке категории');
    });
}

// Показать модальное окно выбора действия при удалении
function showDeleteDirectoryModal(directoryId, directoryName) {
    // Удаляем существующее модальное окно, если есть
    const existingModal = document.getElementById('deleteDirectoryModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Создаём модальное окно
    const modalHtml = `
        <div class="modal fade" id="deleteDirectoryModal" tabindex="-1" aria-labelledby="deleteDirectoryModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-warning">
                        <h5 class="modal-title" id="deleteDirectoryModalLabel">
                            <i class="bi bi-exclamation-triangle me-2"></i>Удаление категории
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Закрыть"></button>
                    </div>
                    <div class="modal-body">
                        <p>Категория <strong>"${escapeHtml(directoryName)}"</strong> содержит вложенные элементы.</p>
                        <p>Что вы хотите сделать?</p>
                    </div>
                    <div class="modal-footer d-flex flex-column gap-2">
                        <button type="button" class="btn btn-primary w-100" onclick="performDeleteDirectory(${directoryId}, 'move_to_root')">
                            <i class="bi bi-box-arrow-up me-2"></i>Переместить всё в корень БЗ
                        </button>
                        <button type="button" class="btn btn-danger w-100" onclick="performDeleteDirectory(${directoryId}, 'delete_all')">
                            <i class="bi bi-trash me-2"></i>Удалить всё безвозвратно
                        </button>
                        <button type="button" class="btn btn-secondary w-100" data-bs-dismiss="modal">
                            Отмена
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = new bootstrap.Modal(document.getElementById('deleteDirectoryModal'));
    modal.show();
}

// Выполнить удаление категории с указанным действием
function performDeleteDirectory(directoryId, action) {
    // Закрываем модальное окно, если открыто
    const modal = document.getElementById('deleteDirectoryModal');
    if (modal) {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    }
    
    fetch(`/kb/directory/${directoryId}/delete/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Если переместили в корень - перезагружаем страницу чтобы увидеть изменения
            if (action === 'move_to_root') {
                window.location.reload();
            } else {
                // Удаляем элемент из DOM
                removeDirectoryFromDOM(directoryId);
            }
        } else {
            alert('Ошибка: ' + (data.error || 'Не удалось удалить категорию'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при удалении категории');
    });
}

// Удалить элемент категории из DOM
function removeDirectoryFromDOM(directoryId) {
    const container = document.querySelector(`.item-name-container[data-directory-id="${directoryId}"]`);
    if (container) {
        const folderItem = container.closest('.folder-item');
        if (folderItem) {
            folderItem.style.transition = 'opacity 0.3s';
            folderItem.style.opacity = '0';
            setTimeout(() => {
                folderItem.remove();
                
                // Проверяем, остались ли ещё папки
                const foldersSection = document.querySelector('.content-section h5.section-header .bi-folder-fill');
                if (foldersSection) {
                    const itemsGrid = foldersSection.closest('.content-section').querySelector('.items-grid');
                    if (itemsGrid && itemsGrid.children.length === 0) {
                        // Удаляем секцию папок, если она пуста
                        foldersSection.closest('.content-section').remove();
                        
                        // Проверяем, пуста ли вся папка
                        const folderContent = document.querySelector('.folder-content');
                        const hasContent = folderContent.querySelector('.content-section');
                        if (!hasContent) {
                            // Показываем сообщение о пустой папке
                            folderContent.innerHTML = `
                                <div class="empty-folder">
                                    <div class="empty-folder-icon">
                                        <i class="bi bi-folder-x"></i>
                                    </div>
                                    <p class="text-muted">Папка пуста</p>
                                    <p class="text-muted small">Создайте категорию, курс, урок или тест в этой папке</p>
                                </div>
                            `;
                        }
                    }
                }
            }, 300);
        }
    }
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
    
    // Обработка клика вне области редактирования или создания
    document.addEventListener('click', function(e) {
        const clickedElement = e.target;
        
        // Проверяем активное создание категории
        const newDirectoryItem = document.querySelector('.new-directory-item');
        if (newDirectoryItem) {
            const isClickInsideNewItem = newDirectoryItem.contains(clickedElement);
            const isClickOnCreateButton = clickedElement.closest('[onclick*="createNewDirectory"]');
            
            if (!isClickInsideNewItem && !isClickOnCreateButton) {
                const input = newDirectoryItem.querySelector('.new-directory-input');
                if (input && !input.value.trim()) {
                    cancelNewDirectory();
                    return;
                }
            }
        }
        
        // Проверяем, есть ли активное редактирование
        const activeForm = document.querySelector('.edit-name-form[style*="inline"]:not(.new-directory-item .edit-name-form)');
        if (!activeForm) return;
        
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


// Модальное окно добавления материалов в курс
document.addEventListener('DOMContentLoaded', function() {
    const addLessonModal = document.getElementById('addLessonModal');
    let currentCourseSlug = null;
    let currentCourseTitle = null;
    
    // Обработчик открытия модального окна
    addLessonModal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        currentCourseSlug = button.getAttribute('data-course-slug');
        currentCourseTitle = button.getAttribute('data-course-title');
        
        // Обновляем заголовок модального окна
        document.getElementById('addLessonModalLabel').textContent = 
            `Добавить в курс: ${currentCourseTitle}`;
        
        // Сбрасываем табы на первую вкладку
        const lessonsTab = document.getElementById('lessons-tab');
        const quizzesTab = document.getElementById('quizzes-tab');
        const lessonsPane = document.getElementById('lessons-pane');
        const quizzesPane = document.getElementById('quizzes-pane');
        
        lessonsTab.classList.add('active');
        quizzesTab.classList.remove('active');
        lessonsPane.classList.add('show', 'active');
        quizzesPane.classList.remove('show', 'active');
        
        // Сбрасываем состояние уроков
        resetLessonsState();
        // Сбрасываем состояние тестов
        resetQuizzesState();
        // Загружаем список доступных уроков
        loadAvailableLessons(currentCourseSlug);
    });
    
    // Обработчик переключения табов
    const quizzesTab = document.getElementById('quizzes-tab');
    if (quizzesTab) {
        // Функция для загрузки тестов
        function handleQuizzesTabLoad() {
            // Проверяем, что вкладка действительно активна
            const quizzesPane = document.getElementById('quizzes-pane');
            if (!quizzesPane || !quizzesPane.classList.contains('active')) {
                return;
            }
            
            // Проверяем, что currentCourseSlug установлен
            if (!currentCourseSlug) {
                console.error('currentCourseSlug не установлен');
                const quizzesLoading = document.getElementById('quizzes-loading');
                const quizzesError = document.getElementById('quizzes-error');
                if (quizzesLoading) quizzesLoading.style.display = 'none';
                if (quizzesError) {
                    quizzesError.textContent = 'Ошибка: не удалось определить курс';
                    quizzesError.style.display = 'block';
                }
                return;
            }
            
            // Загружаем тесты только если контейнер пуст
            const quizzesContainer = document.getElementById('quizzes-container');
            const isEmpty = !quizzesContainer || quizzesContainer.innerHTML.trim() === '';
            
            if (isEmpty) {
                resetQuizzesState();
                loadAvailableQuizzes(currentCourseSlug);
            }
        }
        
        // Обработчик события shown.bs.tab (срабатывает после переключения)
        quizzesTab.addEventListener('shown.bs.tab', handleQuizzesTabLoad);
    }
    
    // Функции для сброса состояния
    function resetLessonsState() {
        document.getElementById('lessons-loading').style.display = 'block';
        document.getElementById('lessons-list').style.display = 'none';
        document.getElementById('lessons-error').style.display = 'none';
        document.getElementById('lessons-empty').style.display = 'none';
        document.getElementById('lessons-container').innerHTML = '';
    }
    
    function resetQuizzesState() {
        document.getElementById('quizzes-loading').style.display = 'block';
        document.getElementById('quizzes-list').style.display = 'none';
        document.getElementById('quizzes-error').style.display = 'none';
        document.getElementById('quizzes-empty').style.display = 'none';
        document.getElementById('quizzes-container').innerHTML = '';
    }
    
    // Функция загрузки списка доступных уроков
    function loadAvailableLessons(courseSlug) {
        fetch(`/courses/course/${courseSlug}/available-lessons/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка загрузки уроков');
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('lessons-loading').style.display = 'none';
                
                if (data.lessons && data.lessons.length > 0) {
                    const container = document.getElementById('lessons-container');
                    container.innerHTML = '';
                    
                    data.lessons.forEach(lesson => {
                        const lessonItem = document.createElement('div');
                        lessonItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
                        lessonItem.innerHTML = `
                            <div>
                                <h6 class="mb-1">${escapeHtml(lesson.title)}</h6>
                                <small class="text-muted">
                                    <i class="bi bi-book"></i> ${escapeHtml(lesson.current_course)} | 
                                    <i class="bi bi-folder"></i> ${escapeHtml(lesson.directory)}
                                </small>
                            </div>
                            <button class="btn btn-sm btn-primary add-lesson-btn" 
                                    data-lesson-id="${lesson.id}"
                                    data-lesson-title="${escapeHtml(lesson.title)}">
                                <i class="bi bi-plus-circle"></i> Добавить
                            </button>
                        `;
                        container.appendChild(lessonItem);
                    });
                    
                    document.getElementById('lessons-list').style.display = 'block';
                    
                    // Добавляем обработчики для кнопок добавления
                    document.querySelectorAll('.add-lesson-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const lessonId = this.getAttribute('data-lesson-id');
                            const lessonTitle = this.getAttribute('data-lesson-title');
                            addLessonToCourse(courseSlug, lessonId, lessonTitle, this);
                        });
                    });
                } else {
                    document.getElementById('lessons-empty').style.display = 'block';
                }
            })
            .catch(error => {
                document.getElementById('lessons-loading').style.display = 'none';
                document.getElementById('lessons-error').textContent = 
                    'Ошибка при загрузке списка уроков: ' + error.message;
                document.getElementById('lessons-error').style.display = 'block';
            });
    }
    
    // Функция загрузки списка доступных тестов
    function loadAvailableQuizzes(courseSlug) {
        if (!courseSlug) {
            console.error('courseSlug не передан в loadAvailableQuizzes');
            document.getElementById('quizzes-loading').style.display = 'none';
            document.getElementById('quizzes-error').textContent = 
                'Ошибка: не указан курс';
            document.getElementById('quizzes-error').style.display = 'block';
            return;
        }
        
        fetch(`/courses/course/${courseSlug}/available-quizzes/`)
            .then(response => {
                if (!response.ok) {
                    // Пытаемся получить текст ошибки
                    return response.text().then(text => {
                        throw new Error(`Ошибка ${response.status}: ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('quizzes-loading').style.display = 'none';
                
                if (data.quizzes && data.quizzes.length > 0) {
                    const container = document.getElementById('quizzes-container');
                    container.innerHTML = '';
                    
                    data.quizzes.forEach(quiz => {
                        const quizItem = document.createElement('div');
                        quizItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
                        quizItem.innerHTML = `
                            <div>
                                <h6 class="mb-1">${escapeHtml(quiz.name)}</h6>
                                <small class="text-muted">
                                    <i class="bi bi-folder"></i> ${escapeHtml(quiz.directory)}
                                </small>
                            </div>
                            <button class="btn btn-sm btn-primary add-quiz-btn" 
                                    data-quiz-id="${quiz.id}"
                                    data-quiz-name="${escapeHtml(quiz.name)}">
                                <i class="bi bi-plus-circle"></i> Добавить
                            </button>
                        `;
                        container.appendChild(quizItem);
                    });
                    
                    document.getElementById('quizzes-list').style.display = 'block';
                    
                    // Добавляем обработчики для кнопок добавления
                    document.querySelectorAll('.add-quiz-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const quizId = this.getAttribute('data-quiz-id');
                            const quizName = this.getAttribute('data-quiz-name');
                            addQuizToCourse(courseSlug, quizId, quizName, this);
                        });
                    });
                } else {
                    document.getElementById('quizzes-empty').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки тестов:', error);
                document.getElementById('quizzes-loading').style.display = 'none';
                document.getElementById('quizzes-error').textContent = 
                    'Ошибка при загрузке списка тестов: ' + error.message;
                document.getElementById('quizzes-error').style.display = 'block';
            });
    }
    
    // Функция добавления урока в курс
    function addLessonToCourse(courseSlug, lessonId, lessonTitle, button) {
        button.disabled = true;
        const originalHtml = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Добавление...';
        
        const formData = new FormData();
        formData.append('lesson_id', lessonId);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        fetch(`/courses/course/${courseSlug}/add-lesson/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.innerHTML = '<i class="bi bi-check-circle"></i> Добавлено';
                button.classList.remove('btn-primary');
                button.classList.add('btn-success');
                
                // Удаляем элемент из списка после успешного добавления
                const lessonItem = button.closest('.list-group-item');
                if (lessonItem) {
                    setTimeout(() => {
                        lessonItem.style.transition = 'opacity 0.3s';
                        lessonItem.style.opacity = '0';
                        setTimeout(() => {
                            lessonItem.remove();
                            // Проверяем, остались ли еще уроки в списке
                            const container = document.getElementById('lessons-container');
                            if (!container || container.children.length === 0) {
                                document.getElementById('lessons-list').style.display = 'none';
                                document.getElementById('lessons-empty').style.display = 'block';
                            }
                        }, 300);
                    }, 500);
                }
            } else {
                button.innerHTML = originalHtml;
                button.disabled = false;
                alert('Ошибка: ' + (data.error || 'Не удалось добавить урок'));
            }
        })
        .catch(error => {
            button.innerHTML = originalHtml;
            button.disabled = false;
            alert('Ошибка при добавлении урока: ' + error.message);
        });
    }
    
    // Функция добавления теста в курс
    function addQuizToCourse(courseSlug, quizId, quizName, button) {
        button.disabled = true;
        const originalHtml = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Добавление...';
        
        const formData = new FormData();
        formData.append('quiz_id', quizId);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        fetch(`/courses/course/${courseSlug}/add-quiz/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.innerHTML = '<i class="bi bi-check-circle"></i> Добавлено';
                button.classList.remove('btn-primary');
                button.classList.add('btn-success');
                
                // Удаляем элемент из списка после успешного добавления
                const quizItem = button.closest('.list-group-item');
                if (quizItem) {
                    setTimeout(() => {
                        quizItem.style.transition = 'opacity 0.3s';
                        quizItem.style.opacity = '0';
                        setTimeout(() => {
                            quizItem.remove();
                            // Проверяем, остались ли еще тесты в списке
                            const container = document.getElementById('quizzes-container');
                            if (!container || container.children.length === 0) {
                                document.getElementById('quizzes-list').style.display = 'none';
                                document.getElementById('quizzes-empty').style.display = 'block';
                            }
                        }, 300);
                    }, 500);
                }
            } else {
                button.innerHTML = originalHtml;
                button.disabled = false;
                alert('Ошибка: ' + (data.error || 'Не удалось добавить тест'));
            }
        })
        .catch(error => {
            button.innerHTML = originalHtml;
            button.disabled = false;
            alert('Ошибка при добавлении теста: ' + error.message);
        });
    }
    
    // Вспомогательная функция для получения CSRF токена
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
    
    // Вспомогательная функция для экранирования HTML
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});