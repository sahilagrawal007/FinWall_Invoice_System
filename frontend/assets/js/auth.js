// Authentication Module
class Auth {
  // Check if user is logged in
  static isLoggedIn() {
    return localStorage.getItem("access_token") !== null;
  }

  // Get current user
  static getUser() {
    const userStr = localStorage.getItem("user");
    return userStr ? JSON.parse(userStr) : null;
  }

  // Get current organization
  static getOrganization() {
    const orgStr = localStorage.getItem("organization");
    return orgStr ? JSON.parse(orgStr) : null;
  }

  // Login
  static async login(email, password) {
    try {
      console.log("[Auth] Attempting login for:", email);

      const response = await api.post("/auth/login", {
        email: email,
        password: password,
      });

      console.log("[Auth] Login response:", response);

      if (response.data && response.data.access_token) {
        // Store token
        localStorage.setItem("access_token", response.data.access_token);

        // Store user info
        localStorage.setItem("user", JSON.stringify(response.data.user));

        // Store current organization
        localStorage.setItem("organization", JSON.stringify(response.data.current_organization));

        console.log("[Auth] Login successful! Token stored.");
        return response.data;
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (error) {
      console.error("[Auth] Login failed:", error);
      throw error;
    }
  }

  // Register
  static async register(email, password, firstName, lastName, organizationName) {
    try {
      console.log("[Auth] Attempting registration for:", email);

      const response = await api.post("/auth/register", {
        email: email,
        password: password,
        first_name: firstName,
        last_name: lastName,
        organization_name: organizationName,
      });

      console.log("[Auth] Registration response:", response);

      if (response.data && response.data.access_token) {
        // Store token
        localStorage.setItem("access_token", response.data.access_token);

        // Store user info
        localStorage.setItem("user", JSON.stringify(response.data.user));

        // Store current organization
        localStorage.setItem("organization", JSON.stringify(response.data.current_organization));

        console.log("[Auth] Registration successful! Token stored.");
        return response.data;
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (error) {
      console.error("[Auth] Registration failed:", error);
      throw error;
    }
  }

  // Logout
  static logout() {
    console.log("[Auth] Logging out...");
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    localStorage.removeItem("organization");
    window.location.href = "login.html";
  }

  // Redirect to login if not authenticated
  static requireAuth() {
    if (!Auth.isLoggedIn()) {
      console.log("[Auth] Not logged in, redirecting to login page");
      window.location.href = "login.html";
    }
  }
}
