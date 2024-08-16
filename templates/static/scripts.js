document.addEventListener('DOMContentLoaded', () => {
    const urlField = document.getElementById('url');
    const urlsField = document.getElementById('urls');
    const submitButton = document.getElementById('submitButton');

    // Функція для перевірки полів
    function checkFields() {
        if (urlField.value.trim() || urlsField.value.trim()) {
            submitButton.disabled = false; // Активувати кнопку
        } else {
            submitButton.disabled = true; // Деактивувати кнопку
        }
    }

    // Перевіряти поля при зміні їх значення
    urlField.addEventListener('input', checkFields);
    urlsField.addEventListener('input', checkFields);

    // Перевірка форми перед відправкою
    document.getElementById('urlForm').addEventListener('submit', async (event) => {
        if (urlField.value.trim() === '' && urlsField.value.trim() === '') {
            event.preventDefault(); // Запобігти відправці форми
            alert('Будь ласка, заповніть хоча б одне з полів.');
        } else {
            await handleSubmit(); // Викликати асинхронну функцію handleSubmit
            return false; // Запобігти звичайній відправці форми
        }
    });
});
