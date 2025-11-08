// --- Переключение между курсами ---
const toggleCoursesBtn = document.getElementById('toggle-courses-btn');
const unfinishedBlock = document.getElementById('unfinished-courses');
const finishedBlock = document.getElementById('finished-courses');

toggleCoursesBtn.addEventListener('click', () => {
    const isFinishedVisible = finishedBlock.style.display === 'block';
    finishedBlock.style.display = isFinishedVisible ? 'none' : 'block';
    unfinishedBlock.style.display = isFinishedVisible ? 'block' : 'none';
    toggleCoursesBtn.textContent = isFinishedVisible 
        ? 'Показать завершенные курсы' 
        : 'Показать незавершенные курсы';
});

// --- Переключение между тестами и их отображением ---
const toggleQuizzesBtn = document.getElementById('toggle-quizzes-btn');
// Найдём нужный блок с тестами (вторая .container.mt-4)
const containers = document.querySelectorAll('.container.mt-4');
const quizzesSection = containers[1]; // второй блок - история тестов

// По умолчанию скрываем блок с тестами
quizzesSection.style.display = 'none';
toggleQuizzesBtn.textContent = 'Показать тесты';

toggleQuizzesBtn.addEventListener('click', () => {
    const isVisible = quizzesSection.style.display === 'block';
    quizzesSection.style.display = isVisible ? 'none' : 'block';
    toggleQuizzesBtn.textContent = isVisible ? 'Показать тесты' : 'Скрыть тесты';
});

// --- Переключение режимов редактирования профиля ---
const editProfileBtn = document.getElementById('edit-profile-btn');
const cancelEditBtn = document.getElementById('cancel-edit-btn');
const editProfileForm = document.getElementById('edit-profile-form');
const progressBar = document.querySelector('.progress-bar-user');

editProfileBtn.addEventListener('click', function() {
    editProfileForm.style.display = 'block';
    editProfileBtn.style.display = 'none';
    toggleCoursesBtn.style.display = 'none';
    toggleQuizzesBtn.style.display = 'none';
    progressBar.style.display = 'none';
});

cancelEditBtn.addEventListener('click', function(event) {
    event.preventDefault();
    editProfileForm.style.display = 'none';
    editProfileBtn.style.display = 'block';
    toggleCoursesBtn.style.display = 'block';
    toggleQuizzesBtn.style.display = 'block';
    progressBar.style.display = 'block';
});
