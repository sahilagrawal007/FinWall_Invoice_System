// Currently, it is not referenced in index.html, I am using jQuery.load(). We can shift to this, if needed.
// 1. Define the Sidebar Component
class AppSidebar extends HTMLElement {
  async connectedCallback() {
    try {
      const response = await fetch("components/sidebar.html");
      const content = await response.text();
      // Inject the content directly
      this.innerHTML = content;
      // FIX: Ensure the element itself acts as a full-height container
      this.classList.add("h-full", "flex", "flex-col");
    } catch (err) {
      console.error("Error loading sidebar:", err);
    }
  }
}

// 2. Define the Header Component
class AppHeader extends HTMLElement {
  async connectedCallback() {
    try {
      const response = await fetch("components/header.html");
      this.innerHTML = await response.text();
    } catch (err) {
      console.error("Error loading header:", err);
    }
  }
}

// 3. Define the Right Panel Component
class AppRightPanel extends HTMLElement {
  async connectedCallback() {
    try {
      const response = await fetch("components/right-panel.html");
      this.innerHTML = await response.text();
    } catch (err) {
      console.error("Error loading right panel:", err);
    }
  }
}

// Register the custom tags
customElements.define("app-sidebar", AppSidebar);
customElements.define("app-header", AppHeader);
customElements.define("app-right-panel", AppRightPanel);