
document.addEventListener('DOMContentLoaded', () => {

    const fname = document.getElementById("fname");
    const email = document.getElementById("email");
    const submit = document.getElementById("Continue");
    const passwordBtn = document.querySelectorAll('.toggle-password');


    if (window.location.pathname == `/register/step2`) {

        if (window.history.replaceState) {
            // Prevent resubmission of form data on page refresh
            window.history.replaceState(null, null, window.location.href);
            
        }
        
        //password validation
        const createBtn = document.getElementById("Create");
        passwordBtn.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.getAttribute('data-target');
                const input = document.getElementById(target);
                const icon = btn.querySelector('i');

                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.replace('fa-eye', 'fa-eye-slash');
                }

                else {
                    input.type = 'password';
                    icon.replace('fa-eye-slash', 'fa-eye');
                }



            });
        });
            
    }

    else {
        if (window.history.replaceState) {
            // Prevent resubmission of form data on page refresh
            window.history.replaceState(null, null, window.location.href);
        }
        fname.addEventListener('input', input);

        email.addEventListener('input', input);

        submit.addEventListener("click", () => {

            document.querySelectorAll(".page").forEach(element => {
                element.classList.add("change");
            });

            document.querySelector(".transfer").style.backgroundColor = "var(--color-primary)";

            document.querySelector(".cs").innerHTML = `<div class="rounded-circle d-flex align-items-center justify-content-center text-white cs"><p>&#10004</p></div>`;

            if ((fname.value.trim() == "" || email.value.trim() == "") && submit.disabled == false) {
                submit.disabled = true;
                document.querySelector(".transfer").style.backgroundColor = "var(--border-color)";
                document.querySelector(".cs").innerHTML = `<div class="rounded-circle d-flex align-items-center justify-content-center text-white cs">1</div>`
                document.querySelectorAll(".page").forEach(element => {
                    element.classList.remove("change");
                });
            }
        });
    }
});

function input() {
    const submit = document.getElementById("Continue");
    submit.disabled = fname.value.trim() == "" || email.value.trim() == "";
}

