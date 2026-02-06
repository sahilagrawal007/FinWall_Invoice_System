// API Configuration
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

// API Client Class
class APIClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Get auth token from localStorage
  getToken() {
    return localStorage.getItem("access_token");
  }

  // Get headers with auth token
  getHeaders() {
    const headers = {
      "Content-Type": "application/json",
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  } 

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: this.getHeaders(),
    };

    try {
      console.log(`[API] ${options.method || "GET"} ${url}`);
      const response = await fetch(url, config);

      // Log response status
      console.log(`[API] Response Status: ${response.status}`);

      // Handle unauthorized
      if (response.status === 401) {
        console.error("[API] Unauthorized - redirecting to login");
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        localStorage.removeItem("organization");
        window.location.href = "login.html";
        throw new Error("Unauthorized");
      }

      const data = await response.json();

      if (!response.ok) {
        console.error("[API] Error response:", data);
        throw new Error(data.error || data.detail || "API request failed");
      }

      console.log("[API] Success:", data);
      return data;
    } catch (error) {
      console.error("[API] Request failed:", error);
      throw error;
    }
  }

  // GET request
  async get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  }

  // POST request
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // PATCH request
  async patch(endpoint, data) {
    return this.request(endpoint, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
}

// Create global API instance
const api = new APIClient();
