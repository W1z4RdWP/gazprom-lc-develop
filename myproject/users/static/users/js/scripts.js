document.addEventListener('DOMContentLoaded', () => {
    // --- Переключение между курсами ---
    const toggleCoursesBtn = document.getElementById('toggle-courses-btn');
    const unfinishedBlock = document.getElementById('unfinished-courses');
    const finishedBlock = document.getElementById('finished-courses');

    if (toggleCoursesBtn) {
        toggleCoursesBtn.addEventListener('click', () => {
            const isFinishedVisible = finishedBlock.style.display === 'block';
            finishedBlock.style.display = isFinishedVisible ? 'none' : 'block';
            unfinishedBlock.style.display = isFinishedVisible ? 'block' : 'none';
            toggleCoursesBtn.textContent = isFinishedVisible 
                ? 'Показать завершенные курсы' 
                : 'Показать незавершенные курсы';
        });
    }

    // --- Элементы для работы с тестами ---
    const toggleQuizzesBtn = document.getElementById('toggle-quizzes-btn');
    const quizzesSection = document.querySelector('.quiz-history-container');
    
    // --- Инициализация состояния тестов ---
    let isQuizzesVisible = localStorage.getItem('quizzesVisible') === 'true';
    if (quizzesSection) {
        quizzesSection.style.display = isQuizzesVisible ? 'block' : 'none';
        if (toggleQuizzesBtn) {
            toggleQuizzesBtn.textContent = isQuizzesVisible ? 'Скрыть тесты' : 'Показать тесты';
        }
    }

    // --- Обработчик кнопки тестов ---
    if (toggleQuizzesBtn && quizzesSection) {
        toggleQuizzesBtn.addEventListener('click', () => {
            isQuizzesVisible = !isQuizzesVisible;
            quizzesSection.style.display = isQuizzesVisible ? 'block' : 'none';
            toggleQuizzesBtn.textContent = isQuizzesVisible ? 'Скрыть тесты' : 'Показать тесты';
            localStorage.setItem('quizzesVisible', isQuizzesVisible);
        });
    }

    // --- Пагинация с AJAX ---
    if (quizzesSection) {
        quizzesSection.addEventListener('click', async (e) => {
            const target = e.target.closest('.page-link');
            if (!target) return;
            
            e.preventDefault();
            
            // Активируем блок если скрыт
            if (!isQuizzesVisible) {
                isQuizzesVisible = true;
                quizzesSection.style.display = 'block';
                if (toggleQuizzesBtn) {
                    toggleQuizzesBtn.textContent = 'Скрыть тесты';
                    localStorage.setItem('quizzesVisible', true);
                }
            }

            const url = new URL(target.href);
            const page = url.searchParams.get('page');
            
            try {
                const response = await fetch(`?page=${page}`, {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                const html = await response.text();
                
                document.getElementById('quiz-history-content').innerHTML = html;
                history.pushState(null, null, `?page=${page}`);
            } catch (error) {
                console.error('Ошибка загрузки:', error);
                document.getElementById('quiz-history-content').innerHTML = `
                    <div class="alert alert-danger mt-3">
                        Ошибка загрузки данных. Попробуйте обновить страницу.
                    </div>
                `;
            }
        });
    }

    // --- Обработка истории браузера ---
    window.addEventListener('popstate', async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page') || 1;
        
        try {
            const response = await fetch(`?page=${page}`, {
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });
            const html = await response.text();
            
            if (quizzesSection) {
                document.getElementById('quiz-history-content').innerHTML = html;
                quizzesSection.style.display = 'block';
                isQuizzesVisible = true;
                if (toggleQuizzesBtn) {
                    toggleQuizzesBtn.textContent = 'Скрыть тесты';
                    localStorage.setItem('quizzesVisible', true);
                }
            }
        } catch (error) {
            console.error('Ошибка загрузки:', error);
        }
    });

    // --- Переключение режимов редактирования профиля ---
    const editProfileBtn = document.getElementById('edit-profile-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const editProfileForm = document.getElementById('edit-profile-form');
    const experienceSection = document.querySelector('.experience-section');
    const profileActions = document.querySelector('.profile-actions');
    const profileHeader = document.querySelector('.profile-header');

    if (editProfileBtn && cancelEditBtn) {
        editProfileBtn.addEventListener('click', function() {
            editProfileForm.style.display = 'block';
            editProfileBtn.style.display = 'none';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'none';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'none';
            if (experienceSection) experienceSection.style.display = 'none';
            if (profileHeader) profileHeader.style.display = 'none';
            if (profileActions) {
                const otherButtons = profileActions.querySelectorAll('.action-btn:not(#edit-profile-btn)');
                otherButtons.forEach(btn => btn.style.display = 'none');
            }
        });

        cancelEditBtn.addEventListener('click', function(event) {
            event.preventDefault();
            editProfileForm.style.display = 'none';
            editProfileBtn.style.display = 'block';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'block';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'block';
            if (experienceSection) experienceSection.style.display = 'block';
            if (profileHeader) profileHeader.style.display = 'flex';
            if (profileActions) {
                const otherButtons = profileActions.querySelectorAll('.action-btn:not(#edit-profile-btn)');
                otherButtons.forEach(btn => btn.style.display = 'block');
            }
        });
    }
});















// // --- Переключение между курсами --- old
// const toggleCoursesBtn = document.getElementById('toggle-courses-btn');
// const unfinishedBlock = document.getElementById('unfinished-courses');
// const finishedBlock = document.getElementById('finished-courses');

// toggleCoursesBtn.addEventListener('click', () => {
//     const isFinishedVisible = finishedBlock.style.display === 'block';
//     finishedBlock.style.display = isFinishedVisible ? 'none' : 'block';
//     unfinishedBlock.style.display = isFinishedVisible ? 'block' : 'none';
//     toggleCoursesBtn.textContent = isFinishedVisible 
//         ? 'Показать завершенные курсы' 
//         : 'Показать незавершенные курсы';
// });

// // --- Переключение между тестами и их отображением ---
// const toggleQuizzesBtn = document.getElementById('toggle-quizzes-btn');
// // Найдём нужный блок с тестами (вторая .container.mt-4)
// const containers = document.querySelectorAll('.container.mt-4');
// const quizzesSection = containers[1]; // второй блок - история тестов

// // По умолчанию скрываем блок с тестами
// quizzesSection.style.display = 'none';
// toggleQuizzesBtn.textContent = 'Показать тесты';

// toggleQuizzesBtn.addEventListener('click', () => {
//     const isVisible = quizzesSection.style.display === 'block';
//     quizzesSection.style.display = isVisible ? 'none' : 'block';
//     toggleQuizzesBtn.textContent = isVisible ? 'Показать тесты' : 'Скрыть тесты';
// });

// // --- Переключение режимов редактирования профиля ---
// const editProfileBtn = document.getElementById('edit-profile-btn');
// const cancelEditBtn = document.getElementById('cancel-edit-btn');
// const editProfileForm = document.getElementById('edit-profile-form');
// const progressBar = document.querySelector('.progress-bar-user');

// editProfileBtn.addEventListener('click', function() {
//     editProfileForm.style.display = 'block';
//     editProfileBtn.style.display = 'none';
//     toggleCoursesBtn.style.display = 'none';
//     toggleQuizzesBtn.style.display = 'none';
//     progressBar.style.display = 'none';
// });

// cancelEditBtn.addEventListener('click', function(event) {
//     event.preventDefault();
//     editProfileForm.style.display = 'none';
//     editProfileBtn.style.display = 'block';
//     toggleCoursesBtn.style.display = 'block';
//     toggleQuizzesBtn.style.display = 'block';
//     progressBar.style.display = 'block';
// });
