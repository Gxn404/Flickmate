document.addEventListener('DOMContentLoaded', () => {

    const passwordChange = document.querySelector('.pass-change');
    const passwordBtn = document.querySelector('.btn');

    passwordBtn.addEventListener('click', () => {

        const passwordInput = document.querySelector('input[name="password"]');

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            passwordChange.classList.replace('fa-eye', 'fa-eye-slash');
        }

        else {
            passwordInput.type = 'password';
            passwordChange.classList.replace('fa-eye', 'fa-eye-slash');
            passwordChange.classList.add('fa-eye');
        }
    });

});
