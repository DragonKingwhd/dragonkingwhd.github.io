// ========== Navigation ==========
document.addEventListener('DOMContentLoaded', () => {
  const sidebarLinks = document.querySelectorAll('.sidebar-link');
  const sections = document.querySelectorAll('.section');
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const sidebar = document.querySelector('.sidebar');
  const progressFill = document.querySelector('.progress-bar-fill');
  const progressText = document.querySelector('.progress-text');

  // Load completion state
  const completedSections = JSON.parse(localStorage.getItem('completedSections') || '{}');

  // Restore completed state
  Object.keys(completedSections).forEach(id => {
    if (completedSections[id]) {
      const link = document.querySelector(`.sidebar-link[data-section="${id}"]`);
      if (link) link.classList.add('completed');
      const checkbox = document.querySelector(`#complete-${id}`);
      if (checkbox) {
        checkbox.checked = true;
        checkbox.closest('.section-complete').classList.add('checked');
      }
    }
  });

  updateProgress();

  // Navigation click
  sidebarLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('data-section');
      navigateTo(targetId);
      if (window.innerWidth <= 900) sidebar.classList.remove('open');
    });
  });

  function navigateTo(id) {
    sidebarLinks.forEach(l => l.classList.remove('active'));
    sections.forEach(s => s.classList.remove('active'));

    const targetLink = document.querySelector(`.sidebar-link[data-section="${id}"]`);
    const targetSection = document.getElementById(id);

    if (targetLink) targetLink.classList.add('active');
    if (targetSection) targetSection.classList.add('active');

    window.scrollTo(0, 0);
    history.replaceState(null, '', `#${id}`);
  }

  // Mobile menu
  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }

  // Handle initial hash
  const hash = window.location.hash.slice(1);
  if (hash) {
    navigateTo(hash);
  } else {
    navigateTo('home');
  }

  // Expose navigateTo globally
  window.navigateTo = navigateTo;

  // ========== Section completion checkboxes ==========
  document.querySelectorAll('.section-complete input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      const sectionId = cb.id.replace('complete-', '');
      completedSections[sectionId] = cb.checked;
      localStorage.setItem('completedSections', JSON.stringify(completedSections));

      const link = document.querySelector(`.sidebar-link[data-section="${sectionId}"]`);
      if (cb.checked) {
        link?.classList.add('completed');
        cb.closest('.section-complete').classList.add('checked');
      } else {
        link?.classList.remove('completed');
        cb.closest('.section-complete').classList.remove('checked');
      }
      updateProgress();
    });
  });

  function updateProgress() {
    const total = document.querySelectorAll('.section-complete input[type="checkbox"]').length;
    const done = Object.values(completedSections).filter(v => v).length;
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    if (progressFill) progressFill.style.width = pct + '%';
    if (progressText) progressText.textContent = `${done}/${total} 已完成`;
  }
});

// ========== Answer Toggle ==========
function toggleAnswer(btn) {
  const content = btn.nextElementSibling;
  if (content.classList.contains('show')) {
    content.classList.remove('show');
    btn.textContent = '显示答案';
  } else {
    content.classList.add('show');
    btn.textContent = '隐藏答案';
  }
}

// ========== Quiz ==========
function selectQuiz(el, correct, explanation) {
  const quiz = el.closest('.quiz');
  const options = quiz.querySelectorAll('.quiz-option');
  const explEl = quiz.querySelector('.quiz-explanation');

  // Prevent re-answering
  if (quiz.classList.contains('answered')) return;
  quiz.classList.add('answered');

  options.forEach(opt => {
    if (opt.getAttribute('data-correct') === 'true') {
      opt.classList.add('correct');
    }
  });

  if (!correct) {
    el.classList.add('wrong');
  }

  if (explEl) {
    explEl.classList.add('show');
  }
}

// ========== Code Copy ==========
function copyCode(btn) {
  const block = btn.closest('.code-block');
  const code = block.querySelector('pre').textContent;
  navigator.clipboard.writeText(code).then(() => {
    const orig = btn.textContent;
    btn.textContent = '已复制!';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  });
}

// ========== Tabs ==========
function switchTab(btn, groupId) {
  const group = document.getElementById(groupId);
  const tabId = btn.getAttribute('data-tab');

  group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  group.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

  btn.classList.add('active');
  const target = group.querySelector(`#${tabId}`);
  if (target) target.classList.add('active');
}
