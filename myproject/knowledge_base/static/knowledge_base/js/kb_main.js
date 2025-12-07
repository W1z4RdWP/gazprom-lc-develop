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
                
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(addLessonModal);
                    modal.hide();
                    window.location.reload();
                }, 1000);
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
                
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(addLessonModal);
                    modal.hide();
                    window.location.reload();
                }, 1000);
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