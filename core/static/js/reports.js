// search.js

document.addEventListener("DOMContentLoaded", function () {
  // Get all search boxes with class 'universal-search'
  const searchBoxes = document.querySelectorAll(".universal-search");

  searchBoxes.forEach(searchBox => {
    searchBox.addEventListener("keyup", function () {
      const searchValue = this.value.toLowerCase();

      // Find the closest table to this search box
      const table = this.closest(".attendance-box")?.querySelector("table");
      if (!table) return;

      const rows = table.querySelectorAll("tbody tr");

      rows.forEach(row => {
        const rowText = row.innerText.toLowerCase();
        row.style.display = rowText.includes(searchValue) ? "" : "none";
      });
    });
  });
});
// student_search.js
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.querySelector(".universal-search");
  const studentCards = document.querySelectorAll(".student-card");

  if (!searchInput) return;

  searchInput.addEventListener("keyup", function () {
    const searchValue = this.value.toLowerCase();

    studentCards.forEach(card => {
      const cardText = card.innerText.toLowerCase();
      card.style.display = cardText.includes(searchValue) ? "" : "none";
    });
  });
});
