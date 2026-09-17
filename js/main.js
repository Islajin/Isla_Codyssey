const GITHUB_USERNAME = "Islajin";
const GITHUB_API_URL = `https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=100`;
const CACHE_KEY = "github-projects-cache";
const CACHE_TIME = 60 * 60 * 1000;

const pageState = {
  theme: "light",
  menuOpen: false,
  projects: {
    status: "loading",
    items: [],
    selectedLanguage: "All",
    error: "",
  },
  formErrors: {
    name: "",
    email: "",
    message: "",
  },
};

const dom = {
  root: document.documentElement,
  header: document.querySelector("#site-header"),
  themeToggle: document.querySelector("#theme-toggle"),
  menuToggle: document.querySelector("#menu-toggle"),
  navMenu: document.querySelector("#nav-menu"),
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

const getInitialTheme = () => {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

const renderTheme = () => {
  const isDark = pageState.theme === "dark";
  dom.root.dataset.theme = pageState.theme;
  dom.themeToggle.setAttribute("aria-label", `${isDark ? "라이트" : "다크"} 모드로 전환`);
};

const setTheme = (theme, save = true) => {
  pageState.theme = theme;
  if (save) localStorage.setItem("theme", theme);
  renderTheme();
};

const toggleTheme = () => {
  setTheme(pageState.theme === "dark" ? "light" : "dark");
};

const renderMenu = () => {
  dom.navMenu.classList.toggle("active", pageState.menuOpen);
  dom.menuToggle.classList.toggle("active", pageState.menuOpen);
  dom.menuToggle.setAttribute("aria-expanded", String(pageState.menuOpen));
  dom.menuToggle.setAttribute("aria-label", pageState.menuOpen ? "메뉴 닫기" : "메뉴 열기");
};

const toggleMenu = () => {
  pageState.menuOpen = !pageState.menuOpen;
  renderMenu();
};

const closeMenu = () => {
  pageState.menuOpen = false;
  renderMenu();
};

const smoothScroll = (event) => {
  const href = event.currentTarget.getAttribute("href");
  if (!href?.startsWith("#")) return;

  const target = document.querySelector(href);
  if (!target) return;

  event.preventDefault();
  target.scrollIntoView({ behavior: "smooth" });
  closeMenu();
};

const updateScrollUI = () => {
  dom.header.classList.toggle("scrolled", window.scrollY >= 60);
  dom.scrollTop.classList.toggle("visible", window.scrollY >= 300);
};

const getCachedProjects = () => {
  try {
    const cache = JSON.parse(localStorage.getItem(CACHE_KEY));
    if (!cache || Date.now() - cache.savedAt > CACHE_TIME) return null;
    return cache.items;
  } catch {
    localStorage.removeItem(CACHE_KEY);
    return null;
  }
};

const saveProjects = (items) => {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ items, savedAt: Date.now() }));
  } catch {
    // 캐시 저장에 실패해도 API 결과는 정상적으로 표시한다.
  }
};

const getLanguages = () => [
  "All",
  ...new Set(pageState.projects.items.map(({ language }) => language).filter(Boolean)),
];

const renderFilters = () => {
  const { status, items, selectedLanguage } = pageState.projects;
  if (status !== "success" || items.length === 0) {
    dom.projectFilters.innerHTML = "";
    return;
  }

  dom.projectFilters.innerHTML = getLanguages()
    .map(
      (language) => `
        <button
          class="filter-button${selectedLanguage === language ? " active" : ""}"
          type="button"
          data-language="${escapeHtml(language)}"
          aria-pressed="${selectedLanguage === language}"
        >
          ${escapeHtml(language === "All" ? "전체" : language)}
        </button>
      `,
    )
    .join("");
};

const createProjectCard = ({ name, description, html_url: url, language, stargazers_count: stars }) => `
  <article class="project-card">
    <span class="project-language">${escapeHtml(language || "Other")}</span>
    <h3>${escapeHtml(name)}</h3>
    <p>${escapeHtml(description || "프로젝트 설명이 없습니다.")}</p>
    <div class="project-footer">
      <span>★ ${stars}</span>
      <a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">저장소 보기 ↗</a>
    </div>
  </article>
`;

const renderProjects = () => {
  const { status, items, selectedLanguage, error } = pageState.projects;
  dom.projectsGrid.innerHTML = "";
  renderFilters();

  if (status === "loading") {
    dom.projectsStatus.innerHTML = `
      <div class="status-content">
        <span class="spinner" aria-hidden="true"></span>
        <span>로딩 중...</span>
      </div>
    `;
    return;
  }

  if (status === "error") {
    dom.projectsStatus.innerHTML = `
      <div class="status-content">
        <strong>프로젝트를 불러올 수 없습니다.</strong>
        <span>${escapeHtml(error)}</span>
        <button id="retry-projects" class="retry-button" type="button">다시 시도</button>
      </div>
    `;
    document.querySelector("#retry-projects").addEventListener("click", () => fetchProjects(true));
    return;
  }

  const visibleProjects =
    selectedLanguage === "All"
      ? items
      : items.filter(({ language }) => language === selectedLanguage);

  if (visibleProjects.length === 0) {
    dom.projectsStatus.innerHTML = "<p>표시할 프로젝트가 없습니다.</p>";
    return;
  }

  dom.projectsStatus.innerHTML = "";
  dom.projectsGrid.innerHTML = visibleProjects.map(createProjectCard).join("");
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
    const response = await fetch(GITHUB_API_URL);
    if (!response.ok) {
      if (response.status === 403 || response.status === 429) {
        throw new Error("GitHub API 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.");
      }
      throw new Error(`GitHub API 오류: ${response.status}`);
    }

    const repositories = await response.json();
    pageState.projects.items = repositories;
    pageState.projects.status = "success";
    saveProjects(repositories);
  } catch (error) {
    pageState.projects.status = "error";
    pageState.projects.error = error.message || "네트워크 연결을 확인해 주세요.";
  }

  renderProjects();
};

const selectLanguage = (event) => {
  const button = event.target.closest("[data-language]");
  if (!button) return;

  pageState.projects.selectedLanguage = button.dataset.language;
  renderProjects();
};

const validateField = (name, value) => {
  const trimmedValue = value.trim();
  if (!trimmedValue) return "필수 입력 항목입니다.";
  if (name === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedValue)) {
    return "올바른 이메일 형식을 입력해 주세요.";
  }
  return "";
};

const renderFieldError = (name) => {
  const field = dom.contactForm.elements[name];
  const errorElement = document.querySelector(`#${name}-error`);
  const error = pageState.formErrors[name];

  field.classList.toggle("invalid", Boolean(error));
  field.setAttribute("aria-invalid", String(Boolean(error)));
  errorElement.textContent = error;
};

const handleInput = (event) => {
  const { name, value } = event.target;
  if (!(name in pageState.formErrors)) return;

  pageState.formErrors[name] = validateField(name, value);
  renderFieldError(name);
  dom.formStatus.textContent = "";
  dom.formStatus.classList.remove("error");
};

const submitForm = (event) => {
  event.preventDefault();

  const formData = new FormData(dom.contactForm);
  Object.keys(pageState.formErrors).forEach((name) => {
    pageState.formErrors[name] = validateField(name, String(formData.get(name) || ""));
    renderFieldError(name);
  });

  const hasError = Object.values(pageState.formErrors).some(Boolean);
  if (hasError) {
    dom.formStatus.textContent = "입력한 내용을 확인해 주세요.";
    dom.formStatus.classList.add("error");
    dom.contactForm.querySelector(".invalid")?.focus();
    return;
  }

  dom.formStatus.classList.remove("error");
  dom.formStatus.textContent = "문의가 정상적으로 작성되었습니다.";
  dom.contactForm.reset();
};

const startTyping = () => {
  const sentence = "HTML, CSS, JavaScript로 웹의 기본기를 쌓고 있습니다.";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    dom.typingText.textContent = sentence;
    return;
  }

  let index = 0;
  const type = () => {
    dom.typingText.textContent = sentence.slice(0, index);
    index += 1;
    if (index <= sentence.length) window.setTimeout(type, 70);
  };
  type();
};

const startRevealAnimation = () => {
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

  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
};

const initializeEvents = () => {
  dom.themeToggle.addEventListener("click", toggleTheme);
  dom.menuToggle.addEventListener("click", toggleMenu);
  document.querySelectorAll('a[href^="#"]').forEach((link) => link.addEventListener("click", smoothScroll));
  dom.projectFilters.addEventListener("click", selectLanguage);
  dom.contactForm.addEventListener("input", handleInput);
  dom.contactForm.addEventListener("submit", submitForm);
  dom.scrollTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  window.addEventListener("scroll", updateScrollUI, { passive: true });
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 768 && pageState.menuOpen) closeMenu();
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
  startRevealAnimation();
  startTyping();
  fetchProjects();
};

initializePage();
