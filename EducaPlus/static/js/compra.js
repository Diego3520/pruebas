function luhnCheck(cardNumber) {
    let sum = 0;
    let shouldDouble = false;
    cardNumber = cardNumber.toString();
    for (let i = cardNumber.length - 1; i >= 0; i--) {
        let digit = parseInt(cardNumber.charAt(i));

        if (shouldDouble) {
            if ((digit *= 2) > 9) digit -= 9;
        }

        sum += digit;
        shouldDouble = !shouldDouble;
    }
    return (sum % 10) === 0;
}

function validateExpiryDate(input) {
    // Obtén la fecha actual
    let currentDate = new Date();
    let currentMonth = Number(currentDate.getMonth() + 1); // Los meses en JavaScript van de 0 a 11
    let currentYear = Number(currentDate.getFullYear().toString().substr(-2)); // Obtén los últimos dos dígitos del año

    // Obtén el mes y el año de la fecha de vencimiento ingresada
    let [expiryMonth, expiryYear] = input.value.split('/').map(Number);

    // Comprueba si la fecha de vencimiento es una fecha pasada
    if (expiryYear < currentYear || (expiryYear === currentYear && expiryMonth < currentMonth)) {
        input.setCustomValidity('La fecha de vencimiento no puede ser una fecha pasada.');
    } else {
        input.setCustomValidity('');
    }
}

document.addEventListener("DOMContentLoaded", function () {
        var notificationElement = document.getElementById('notificationContent');
        var notification = new bootstrap.Toast(notificationElement);
        var cursoPrecio = document.getElementById('curso-precio').value;

        if (cursoPrecio == 0) {
            document.getElementById('cardName').required = false;
            document.getElementById('cardNumber').required = false;
            document.getElementById('expiryDate').required = false;
            document.getElementById('cvv').required = false;
        }

        function hideNotification() {
            notification.hide();
        }

        function showNotification() {
            notification.show();
            setTimeout(hideNotification, 5000); // Oculta la notificación después de 5 segundos
        }

        const form = document.querySelector(".small-form");
        const cardNumberField = document.querySelector("#cardNumber");
        const expiryDateField = document.querySelector("#expiryDate"); // Asegúrate de seleccionar el campo correcto
        const cvvField = document.querySelector("#cvv"); // Asegúrate de seleccionar el campo correcto

        if (form && cardNumberField && expiryDateField && cvvField) { // Asegúrate de que los campos necesarios existan
            cardNumberField.addEventListener("keypress", function (event) {
                const char = String.fromCharCode(event.which);
                if (!/\d/.test(char) || char.toLowerCase() === 'e') {
                    event.preventDefault();
                }
            });

            cardNumberField.addEventListener("input", function () {
                const cardNumber = cardNumberField.value.replace(/\D/g, '');
                if (!luhnCheck(cardNumber)) {
                    cardNumberField.setCustomValidity("Por favor, introduce un número de tarjeta válido.");
                } else {
                    cardNumberField.setCustomValidity("");
                }
            });

            expiryDateField.addEventListener("input", function () { // Agrega el evento de entrada al campo de fecha de vencimiento
                validateExpiryDate(expiryDateField);
            });

            cvvField.addEventListener("input", function () { // Agrega el evento de entrada al campo CVV
                const cvv = cvvField.value;
                if (!cvv.match(/^\d{3,4}$/)) {
                    cvvField.setCustomValidity("Por favor, introduce un CVV válido de 3 a 4 dígitos.");
                } else {
                    cvvField.setCustomValidity("");
                }
            });

            cvvField.addEventListener("keypress", function (event) {
                if (!/\d/.test(String.fromCharCode(event.which))) {
                    event.preventDefault();
                }
            });

            form.addEventListener("submit", function (event) {
                if (cursoPrecio != 0) {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                }
                showNotification('Compra realizada', '¡Gracias por tu compra!', 'success');
                form.classList.add('was-validated');
            });

        }
    }
)
;