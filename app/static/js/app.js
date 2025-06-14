// Load Theme on Page Load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);

    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            window.location.href = '/search';
        }); 
    }
});

//Toggle Menu
function toggleMenu() {
 const menuBtn = document.querySelector(".menu-toggle");
      menuBtn.classList.toggle("open");

    // Optional: Close when Offcanvas hides
    const offcanvas = document.getElementById("offcanvasSidebar");
    offcanvas.addEventListener("hidden.bs.offcanvas", () => {
      menuBtn.classList.remove("open");
    });
}

// Toggle Dark Mode
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}