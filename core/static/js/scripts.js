document.addEventListener("DOMContentLoaded", function() {
  function openModal(modal) {
    if (!modal) return;
    modal.style.display = "block";

    // Close buttons inside modal (may be multiple)
    modal.querySelectorAll(".close, .close-btn").forEach(btn => {
      btn.addEventListener('click', () => modal.style.display = 'none');
    });

    // Close when clicking outside the modal
    window.addEventListener('click', function onWindowClick(e) {
      if (e.target === modal) {
        modal.style.display = 'none';
        window.removeEventListener('click', onWindowClick);
      }
    });
  }

  function attachOpenButton(openBtn, modal) {
    if (!openBtn || !modal) return;
    openBtn.addEventListener('click', function(e) {
      e.preventDefault();
      openModal(modal);
    });
  }

  // Add Subject modal (if present)
  const subjectModal = document.getElementById("subjectModal");
  const openSubjectBtn = document.getElementById("openModalSubject");
  attachOpenButton(openSubjectBtn, subjectModal);

  // Assign Teacher modal (if present)
  const assignModal = document.getElementById("assignModal");
  const openAssignBtn = document.getElementById("openModalAssign");
  attachOpenButton(openAssignBtn, assignModal);

  // Edit/Delete modals triggered by data-target attributes
  document.querySelectorAll(".edit-btn, .delete-btn").forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.preventDefault();
      const modalId = btn.dataset.target;
      const modal = document.querySelector(modalId);
      if (modal) openModal(modal);
    });
  });
});
