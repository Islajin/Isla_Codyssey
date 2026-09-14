const GITHUB_USERNAME = "Islajin";
const GITHUB_API_URL = `https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=100`;
const PROJECT_CACHE_KEY = "yeonjin-github-projects";
const PROJECT_CACHE_DURATION = 10 * 60 * 1000;
const FORM_ENDPOINT = "";

const pageState = {
  theme: "light",
  menuOpen: false,
  projects: {
    status: "idle",
    items: [],
    selectedLanguage: "All",
    error: "",
  },
  form: {
    values: { name: "", email: "", message: "" },
    errors: { name: "", email: "", message: "" },
    status: "idle",
  },
};

const dom = {
  root: document.documentElement,
  header: document.querySelector("#site-header"),
  themeToggle: document.querySelector("#theme-toggle"),
  menuToggle: document.querySelector("#menu-toggle"),
  navMenu: document.querySelector("#nav-menu"),
  navLinks: document.querySelectorAll(".nav-link"),
  sections: document.querySelectorAll("main section[id]"),
  scrollTop: document.querySelector("#scroll-top"),
  typingText: document.querySelector("#typing-text"),
  projectFilters: document.querySelector("#project-filters"),
  projectsStatus: document.querySelector("#projects-status"),
  projectsGrid: document.querySelector("#projects-grid"),
  contactForm: document.querySelector("#contact-form"),
  formStatus: document.querySelector("#form-status"),
  currentYear: document.querySelector("#current-year"),
};

const escapeHtml = (value = "") =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const formatDate = (dateString) =>
  new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(dateString));

const getInitialTheme = () => {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

const renderTheme = () => {
  const isDark = pageState.theme === "dark";
  dom.root.dataset.theme = pageState.theme;
  dom.themeToggle.setAttribute("aria-label", `${isDark ? "라이트" : "다크"} 모드로 전환`);
  document.querySelector('meta[name="theme-color"]').content = isDark ? "#171716" : "#fffaf6";
};

const setTheme = (theme, persist = true) => {
  pageState.theme = theme;
  if (persist) localStorage.setItem("theme", theme);
  renderTheme();
};

const toggleTheme = () => {
  setTheme(pageState.theme === "dark" ? "light" : "dark");
};

const renderMenu = () => {
  dom.navMenu.classList.toggle("active", pageState.menuOpen);
  dom.menuToggle.classList.toggle("active", pageState.menuOpen);
  document.body.classList.toggle("menu-open", pageState.menuOpen);
  dom.menuToggle.setAttribute("aria-expanded", String(pageState.menuOpen));
  dom.menuToggle.setAttribute("aria-label", pageState.menuOpen ? "메뉴 닫기" : "메뉴 열기");
};

const setMenuOpen = (isOpen) => {
  pageState.menuOpen = isOpen;
  renderMenu();
};

const scrollToTarget = (event) => {
  const href = event.currentTarget.getAttribute("href");
  if (!href?.startsWith("#")) return;
  const target = document.querySelector(href);
  if (!target) return;

  event.preventDefault();
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  setMenuOpen(false);
};

const updateScrollUI = () => {
  const scrollY = window.scrollY;
  dom.header.classList.toggle("scrolled", scrollY >= 60);
  dom.scrollTop.classList.toggle("visible", scrollY >= 300);

  let activeSectionId = "home";
  dom.sections.forEach((section) => {
    if (scrollY >= section.offsetTop - 180) activeSectionId = section.id;
  });

  dom.navLinks.forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === `#${activeSectionId}`);
  });
};

const getCachedProjects = () => {
  try {
    const cached = JSON.parse(localStorage.getItem(PROJECT_CACHE_KEY));
    if (!cached || Date.now() - cached.savedAt > PROJECT_CACHE_DURATION) return null;
    return cached.items;
  } catch {
    localStorage.removeItem(PROJECT_CACHE_KEY);
    return null;
  }
};

const saveProjectsToCache = (items) => {
  try {
    localStorage.setItem(PROJECT_CACHE_KEY, JSON.stringify({ items, savedAt: Date.now() }));
  } catch {
    // 저장 공간이 차 있어도 API 결과 렌더링은 계속한다.
  }
};

const getLanguages = () => [
  "All",
  ...new Set(pageState.projects.items.map(({ language }) => language).filter(Boolean)),
];

const renderProjectFilters = () => {
  if (pageState.projects.status !== "success" || pageState.projects.items.length === 0) {
    dom.projectFilters.innerHTML = "";
    return;
  }

  dom.projectFilters.innerHTML = getLanguages()
    .map(
      (language) => `
        <button
          class="filter-button${pageState.projects.selectedLanguage === language ? " active" : ""}"
          type="button"
          data-language="${escapeHtml(language)}"
          aria-pressed="${pageState.projects.selectedLanguage === language}"
        >
          ${escapeHtml(language === "All" ? "전체" : language)}
        </button>
      `,
    )
    .join("");
};

const createProjectCard = (repository) => {
  const {
    name,
    description,
    html_url: repositoryUrl,
    homepage,
    language,
    stargazers_count: stars,
    forks_count: forks,
    updated_at: updatedAt,
  } = repository;

  return `
    <article class="project-card">
      <div class="project-card-top">
        <svg class="folder-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 5h6l2 2h10v12H3Z"></path>
        </svg>
        <span class="project-language">${escapeHtml(language || "Other")}</span>
      </div>
      <h3>${escapeHtml(name)}</h3>
      <p>${escapeHtml(description || "GitHub에서 프로젝트의 코드와 상세 내용을 확인해 보세요.")}</p>
      <div class="project-card-footer">
        <div class="project-meta">
          <span title="스타 수">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 2.5 2.9 5.88 6.49.94-4.7 4.58 1.11 6.47L12 17.32l-5.8 3.05 1.11-6.47-4.7-4.58 6.49-.94Z"></path></svg>
            ${stars}
          </span>
          <span title="포크 수">⑂ ${forks}</span>
          <span title="최근 수정일">${escapeHtml(formatDate(updatedAt))}</span>
        </div>
        <div class="project-links">
          ${
            homepage
              ? `<a href="${escapeHtml(homepage)}" target="_blank" rel="noreferrer" aria-label="${escapeHtml(name)} 데모 열기">↗</a>`
              : ""
          }
          <a href="${escapeHtml(repositoryUrl)}" target="_blank" rel="noreferrer" aria-label="${escapeHtml(name)} GitHub 저장소 열기">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 3h6v6M10 14 21 3M18 13v7H4V6h7"></path></svg>
          </a>
        </div>
      </div>
    </article>
  `;
};

const renderProjects = () => {
  const { status, items, selectedLanguage, error } = pageState.projects;
  dom.projectsGrid.innerHTML = "";
  renderProjectFilters();

  if (status === "loading") {
    dom.projectsStatus.innerHTML = `
      <div class="status-content">
        <span class="spinner" aria-hidden="true"></span>
        <span>GitHub 프로젝트를 불러오는 중...</span>
      </div>
    `;
    return;
  }

  if (status === "error") {
    dom.projectsStatus.innerHTML = `
      <div class="status-content">
        <strong>프로젝트를 불러올 수 없습니다.</strong>
        <span>${escapeHtml(error)}</span>
        <button class="retry-button" id="retry-projects" type="button">다시 시도</button>
      </div>
    `;
    document.querySelector("#retry-projects").addEventListener("click", () => fetchProjects(true));
    return;
  }

  const filteredProjects =
    selectedLanguage === "All" ? items : items.filter(({ language }) => language === selectedLanguage);

  if (filteredProjects.length === 0) {
    dom.projectsStatus.innerHTML = "<p>표시할 프로젝트가 없습니다.</p>";
    return;
  }

  dom.projectsStatus.innerHTML = "";
  dom.projectsGrid.innerHTML = filteredProjects.map(createProjectCard).join("");
};

const fetchProjects = async (ignoreCache = false) => {
  pageState.projects.status = "loading";
  pageState.projects.error = "";
  renderProjects();

  const cachedProjects = ignoreCache ? null : getCachedProjects();
  if (cachedProjects) {
    pageState.projects.items = cachedProjects;
    pageState.projects.status = "success";
    renderProjects();
    return;
  }

  try {
    const response = await fetch(GITHUB_API_URL, {
      headers: { Accept: "application/vnd.github+json" },
    });

    if (!response.ok) {
      const isRateLimited = response.status === 403 || response.status === 429;
      throw new Error(
        isRateLimited
          ? "GitHub API 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요."
          : `GitHub API가 ${response.status} 오류를 반환했습니다.`,
      );
    }

    const repositories = await response.json();
    const publicRepositories = repositories.filter(({ fork, archived }) => !fork && !archived);

    pageState.projects.items = publicRepositories;
    pageState.projects.status = "success";
    saveProjectsToCache(publicRepositories);
  } catch (error) {
    pageState.projects.status = "error";
    pageState.projects.error = error.message || "네트워크 연결을 확인해 주세요.";
  }

  renderProjects();
};

const selectProjectLanguage = (event) => {
  const button = event.target.closest("[data-language]");
  if (!button) return;

  pageState.projects.selectedLanguage = button.dataset.language;
  renderProjects();
};

const validateField = (name, value) => {
  const trimmedValue = value.trim();
  if (!trimmedValue) return `${name === "message" ? "메시지를" : name === "email" ? "이메일을" : "이름을"} 입력해 주세요.`;
  if (name === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedValue)) {
    return "올바른 이메일 형식을 입력해 주세요.";
  }
  if (name === "message" && trimmedValue.length < 10) return "메시지는 10자 이상 입력해 주세요.";
  return "";
};

const renderFieldError = (fieldName) => {
  const field = dom.contactForm.elements[fieldName];
  const errorElement = document.querySelector(`#${fieldName}-error`);
  const error = pageState.form.errors[fieldName];

  field.classList.toggle("invalid", Boolean(error));
  field.setAttribute("aria-invalid", String(Boolean(error)));
  field.setAttribute("aria-describedby", `${fieldName}-error`);
  errorElement.textContent = error;
};

const updateFormField = (event) => {
  const { name, value } = event.target;
  if (!(name in pageState.form.values)) return;

  pageState.form.values[name] = value;
  pageState.form.errors[name] = validateField(name, value);
  renderFieldError(name);
  dom.formStatus.textContent = "";
  dom.formStatus.classList.remove("error");
};

const validateForm = () => {
  Object.entries(pageState.form.values).forEach(([name, value]) => {
    pageState.form.errors[name] = validateField(name, value);
    renderFieldError(name);
  });
  return Object.values(pageState.form.errors).every((error) => !error);
};

const submitForm = async (event) => {
  event.preventDefault();

  const formData = new FormData(dom.contactForm);
  pageState.form.values = Object.fromEntries(formData.entries());
  if (!validateForm()) {
    dom.contactForm.querySelector(".invalid")?.focus();
    dom.formStatus.textContent = "입력한 내용을 다시 확인해 주세요.";
    dom.formStatus.classList.add("error");
    return;
  }

  const submitButton = dom.contactForm.querySelector('button[type="submit"]');
  pageState.form.status = "submitting";
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "보내는 중...";
  dom.formStatus.classList.remove("error");

  try {
    if (FORM_ENDPOINT) {
      const response = await fetch(FORM_ENDPOINT, {
        method: "POST",
        body: formData,
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("메시지 전송에 실패했습니다.");
    } else {
      await new Promise((resolve) => window.setTimeout(resolve, 600));
      const { name, email, message } = pageState.form.values;
      const subject = encodeURIComponent(`[Portfolio] ${name}님의 메시지`);
      const body = encodeURIComponent(`${message}\n\n보낸 사람: ${name}\n회신 주소: ${email}`);
      window.location.href = `mailto:?subject=${subject}&body=${body}`;
    }

    pageState.form.status = "success";
    dom.formStatus.textContent = FORM_ENDPOINT
      ? "메시지를 성공적으로 보냈습니다. 곧 확인할게요!"
      : "메일 앱에 메시지를 준비했습니다. 받는 사람을 선택한 뒤 전송해 주세요.";
    dom.contactForm.reset();
    pageState.form.values = { name: "", email: "", message: "" };
  } catch (error) {
    pageState.form.status = "error";
    dom.formStatus.textContent = error.message || "잠시 후 다시 시도해 주세요.";
    dom.formStatus.classList.add("error");
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span").textContent = "메시지 보내기";
  }
};

const startTypingEffect = () => {
  const sentences = [
    "웹의 기본 원리부터 차근차근 쌓아갑니다.",
    "아이디어를 직접 만지고 느낄 수 있는 화면으로 만듭니다.",
    "작은 디테일이 만드는 큰 차이를 좋아합니다.",
  ];

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    dom.typingText.textContent = sentences[0];
    return;
  }

  let sentenceIndex = 0;
  let characterIndex = 0;
  let deleting = false;

  const type = () => {
    const sentence = sentences[sentenceIndex];
    characterIndex += deleting ? -1 : 1;
    dom.typingText.textContent = sentence.slice(0, characterIndex);

    let delay = deleting ? 35 : 65;
    if (!deleting && characterIndex === sentence.length) {
      deleting = true;
      delay = 1800;
    } else if (deleting && characterIndex === 0) {
      deleting = false;
      sentenceIndex = (sentenceIndex + 1) % sentences.length;
      delay = 350;
    }

    window.setTimeout(type, delay);
  };

  type();
};

const initializeRevealAnimation = () => {
  const revealElements = document.querySelectorAll(".reveal");
  const observer = new IntersectionObserver(
    (entries, activeObserver) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("visible");
        activeObserver.unobserve(entry.target);
      });
    },
    { threshold: 0.2 },
  );

  revealElements.forEach((element) => observer.observe(element));
};

const initializeEvents = () => {
  dom.themeToggle.addEventListener("click", toggleTheme);
  dom.menuToggle.addEventListener("click", () => setMenuOpen(!pageState.menuOpen));
  dom.navLinks.forEach((link) => link.addEventListener("click", scrollToTarget));
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    if (!link.classList.contains("nav-link")) link.addEventListener("click", scrollToTarget);
  });
  dom.projectFilters.addEventListener("click", selectProjectLanguage);
  dom.contactForm.addEventListener("input", updateFormField);
  dom.contactForm.addEventListener("submit", submitForm);
  dom.scrollTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  window.addEventListener("scroll", updateScrollUI, { passive: true });
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 768 && pageState.menuOpen) setMenuOpen(false);
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ({ matches }) => {
    if (!localStorage.getItem("theme")) setTheme(matches ? "dark" : "light", false);
  });
};

const initializePage = () => {
  pageState.theme = getInitialTheme();
  renderTheme();
  renderMenu();
  updateScrollUI();
  dom.currentYear.textContent = new Date().getFullYear();
  initializeEvents();
  initializeRevealAnimation();
  startTypingEffect();
  fetchProjects();
};

initializePage();
