// static/js/film_menu.js
function toggleFilmMenu(id, event) {
    event.stopPropagation();
    const menuId = "film-menu-" + id;
    const menu = document.getElementById(menuId);
    if (!menu) return;
  
    const isOpen = menu.classList.contains("open");
    document
      .querySelectorAll(".film-card-menu.open")
      .forEach(m => m.classList.remove("open"));
  
    if (!isOpen) {
      menu.classList.add("open");
    }
  }
  
  window.addEventListener("click", function () {
    document
      .querySelectorAll(".film-card-menu.open")
      .forEach(m => m.classList.remove("open"));
  });