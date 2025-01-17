document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('auth-modal');
    const modalCloseBtn = document.querySelector('.close');
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    const carouselProduct = document.querySelector('#carousel-product');
    const authModalButtons = carouselProduct.querySelectorAll('.auth-modal-btn');
     const productsSection = document.querySelector('.products-page');
     const isAuthenticated = productsSection ? productsSection.dataset.isAuthenticated === 'true' : false;
  
      if (authModalButtons) {
        authModalButtons.forEach(function(button) {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                  modal.style.display = 'block';
            })
         })
      }
  
    modalCloseBtn.onclick = function() {
       modal.style.display = 'none';
    }
  
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
  
    addToCartForms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
           if (!isAuthenticated) {
                 event.preventDefault();
                 modal.style.display = 'block';
             }
  
        })
     })
  });
  
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }