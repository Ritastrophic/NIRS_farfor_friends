document.addEventListener('DOMContentLoaded', function() {
    const addToRequestButtons = document.querySelectorAll('.add-to-request');
    const errorMessage = document.getElementById('error-message'); // Получаем элемент для вывода ошибок

    addToRequestButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const serviceId = this.dataset.serviceId;
            errorMessage.textContent = ''; // Очищаем предыдущие сообщения об ошибках

            // Асинхронный запрос для получения данных услуги
            fetch(`/api/get_service/${serviceId}/`)
                .then(response => response.json())
                .then(serviceData => {
                    // Здесь у вас есть `serviceData` - данные об услуге
                    // Создайте данные для передачи в booking.html через URL

                    // Используем localStorage для хранения данных, чтобы избежать больших URL.
                    localStorage.setItem('serviceData', JSON.stringify(serviceData));
                     window.location.href = `{% url 'booking_view' %}?service_id=${serviceId}`;
                })
                .catch(error => {
                    console.error('Ошибка при получении данных услуги:', error);
                     errorMessage.textContent = 'Произошла ошибка при добавлении услуги.'; // Выводим сообщение в элемент
                    setTimeout(() => {
                           errorMessage.textContent = ''; // Скрываем сообщение через 3 секунды
                      }, 3000);
                });
        });
    });
});