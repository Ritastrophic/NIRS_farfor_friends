document.addEventListener('DOMContentLoaded', function () {
    const workshopSelect = document.getElementById('workshop');
    const dateInput = document.getElementById('date');
    const timeInput = document.getElementById('time');
    const masterSelect = document.getElementById('master');

    function updateMasterOptions() {
        const workshopId = workshopSelect.value;
        const dateValue = dateInput.value;
        const timeValue = timeInput.value;

         if (!workshopId || !dateValue || !timeValue) {
              masterSelect.innerHTML = '<option value="" disabled selected>Выберите мастера</option>';
            return;
         }
        fetch(`/get_available_masters/?workshop_id=${workshopId}&date=${dateValue}&time=${timeValue}`, {
             headers: {
                 'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
                masterSelect.innerHTML = '<option value="" disabled selected>Выберите мастера</option>';
            data.forEach(master => {
               const option = document.createElement('option');
                    option.value = master.id;
                    option.textContent = master.name;
                    masterSelect.appendChild(option);
            });
         }).catch(error => console.error('Ошибка загрузки мастеров:', error));
    }

    workshopSelect.addEventListener('change', updateMasterOptions);
    dateInput.addEventListener('change', updateMasterOptions);
    timeInput.addEventListener('change', updateMasterOptions);
    masterSelect.addEventListener('change', () => {
    console.log(masterSelect.value)
    });
     const checkoutForm = document.getElementById('checkout-form');

    checkoutForm.addEventListener('submit', function (event) {
    event.preventDefault();

        fetch('/service_checkout/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',

           },
        body: new URLSearchParams(new FormData(checkoutForm))
        })
            .then(response => {
                 if (response.ok) {
                        window.location.href = '/order_confirmation';//Перенаправляем на страницу успеха
                    }
                    else{
                        alert('Ошибка оформления заказа')
                    }
                })
                .catch(error => {
                     console.error('Ошибка оформления:', error);
                    alert('Ошибка при оформлении заказа, попробуйте позже');
                });

});

     function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.startsWith(name + '=')) {
                    cookieValue = cookie.substring(name.length + 1);
                    break;
                }
            }
        }
        return cookieValue;
    }
});