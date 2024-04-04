function luhnCheck(cardNumber) {
    let sum = 0;
    let shouldDouble = false;
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

document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector(".small-form");
    const cardNumberField = document.querySelector("#cardNumber");
    if(form && cardNumberField) {
    cardNumberField.addEventListener("input", function() {
        const cardNumber = cardNumberField.value.replace(/\D/g, '');
        if (!luhnCheck(cardNumber)) {
        cardNumberField.setCustomValidity("Por favor, introduce un número de tarjeta válido.");
      } else {
        cardNumberField.setCustomValidity("");
      }
    });

    form.addEventListener("submit", function(event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  }
});