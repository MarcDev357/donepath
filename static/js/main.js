// Persistent Dark Mode Toggle
document.addEventListener("DOMContentLoaded", function () {
  const darkToggle = document.getElementById("darkToggle");
  const body = document.body;

  // Apply saved theme on page load
  if (localStorage.getItem("theme") === "dark") {
    body.classList.add("dark-mode");
    darkToggle.checked = true;
  }

  if (darkToggle) {
    darkToggle.addEventListener("change", () => {
      body.classList.toggle("dark-mode");

      if (body.classList.contains("dark-mode")) {
        localStorage.setItem("theme", "dark");
      } else {
        localStorage.setItem("theme", "light");
      }
    });
  }

  // 🍞 Auto-dismiss Bootstrap toasts after 3 seconds
  const toastElList = [].slice.call(document.querySelectorAll('.toast'));
  toastElList.forEach(function (toastEl) {
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
  });

  // Animate task fade-in
document.querySelectorAll('.task-enter').forEach(el => {
  setTimeout(() => {
    el.classList.add('task-enter-active');
  }, 10); // triggers the transition
});

// Animate delete button (fade-out before redirect)
document.querySelectorAll('a.btn-outline-danger').forEach(btn => {
  btn.addEventListener('click', function (e) {
    e.preventDefault();
    const taskItem = this.closest('li');
    taskItem.classList.add('task-exit-active');
    setTimeout(() => {
      window.location.href = this.href;
    }, 300);
  });
});

});
