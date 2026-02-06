// /**
//  * Utility Functions
//  * Common helper functions used across the application
//  */

// const Utils = {
//   /**
//    * Format date to YYYY-MM-DD
//    */
//   formatDate(date) {
//     if (!date) return "";
//     const d = new Date(date);
//     return d.toISOString().split("T")[0];
//   },

//   /**
//    * Format date to readable format (e.g., "Jan 15, 2026")
//    */
//   formatDateReadable(date) {
//     if (!date) return "";
//     const d = new Date(date);
//     return d.toLocaleDateString("en-US", {
//       year: "numeric",
//       month: "short",
//       day: "numeric",
//     });
//   },

//   /**
//    * Format currency
//    */
//   formatCurrency(amount, currency = "USD") {
//     if (amount === null || amount === undefined) return "$0.00";
//     return new Intl.NumberFormat("en-US", {
//       style: "currency",
//       currency: currency,
//     }).format(amount);
//   },

//   /**
//    * Format number with commas
//    */
//   formatNumber(num) {
//     if (num === null || num === undefined) return "0";
//     return new Intl.NumberFormat("en-US").format(num);
//   },

//   /**
//    * Get status badge color
//    */
//   getStatusColor(status) {
//     const colors = {
//       draft: "gray",
//       sent: "blue",
//       paid: "green",
//       overdue: "red",
//       partially_paid: "yellow",
//       void: "gray",
//       accepted: "green",
//       declined: "red",
//       pending: "yellow",
//     };
//     return colors[status] || "gray";
//   },

//   /**
//    * Get status badge HTML
//    */
//   getStatusBadge(status) {
//     const color = this.getStatusColor(status);
//     const colorClasses = {
//       gray: "bg-gray-100 text-gray-800",
//       blue: "bg-blue-100 text-blue-800",
//       green: "bg-green-100 text-green-800",
//       red: "bg-red-100 text-red-800",
//       yellow: "bg-yellow-100 text-yellow-800",
//     };

//     return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses[color]}">
//       ${status.replace("_", " ").toUpperCase()}
//     </span>`;
//   },

//   /**
//    * Show loading spinner
//    */
//   showLoading(elementId) {
//     const element = document.getElementById(elementId);
//     if (element) {
//       element.innerHTML = `
//         <div class="flex justify-center items-center py-12">
//           <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
//         </div>
//       `;
//     }
//   },

//   /**
//    * Show error message
//    */
//   showError(message, elementId = null) {
//     const errorHtml = `
//       <div class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded relative" role="alert">
//         <span class="block sm:inline">${message}</span>
//       </div>
//     `;

//     if (elementId) {
//       const element = document.getElementById(elementId);
//       if (element) {
//         element.innerHTML = errorHtml;
//       }
//     } else {
//       // Show as toast notification
//       this.showToast(message, "error");
//     }
//   },

//   /**
//    * Show success message
//    */
//   showSuccess(message, elementId = null) {
//     const successHtml = `
//       <div class="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded relative" role="alert">
//         <span class="block sm:inline">${message}</span>
//       </div>
//     `;

//     if (elementId) {
//       const element = document.getElementById(elementId);
//       if (element) {
//         element.innerHTML = successHtml;
//       }
//     } else {
//       // Show as toast notification
//       this.showToast(message, "success");
//     }
//   },

//   /**
//    * Show toast notification
//    */
//   showToast(message, type = "info") {
//     const colors = {
//       success: "bg-green-500",
//       error: "bg-red-500",
//       warning: "bg-yellow-500",
//       info: "bg-blue-500",
//     };

//     const toast = document.createElement("div");
//     toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300`;
//     toast.innerHTML = message;

//     document.body.appendChild(toast);

//     // Auto remove after 3 seconds
//     setTimeout(() => {
//       toast.style.opacity = "0";
//       setTimeout(() => {
//         document.body.removeChild(toast);
//       }, 300);
//     }, 3000);
//   },

//   /**
//    * Debounce function
//    */
//   debounce(func, wait) {
//     let timeout;
//     return function executedFunction(...args) {
//       const later = () => {
//         clearTimeout(timeout);
//         func(...args);
//       };
//       clearTimeout(timeout);
//       timeout = setTimeout(later, wait);
//     };
//   },

//   /**
//    * Validate email
//    */
//   isValidEmail(email) {
//     const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
//     return re.test(email);
//   },

//   /**
//    * Calculate days between dates
//    */
//   daysBetween(date1, date2) {
//     const d1 = new Date(date1);
//     const d2 = new Date(date2);
//     const diffTime = Math.abs(d2 - d1);
//     return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
//   },

//   /**
//    * Get date range for common periods
//    */
//   getDateRange(period) {
//     const today = new Date();
//     const ranges = {
//       today: {
//         start: this.formatDate(today),
//         end: this.formatDate(today),
//       },
//       yesterday: {
//         start: this.formatDate(
//           new Date(today.getTime() - 24 * 60 * 60 * 1000)
//         ),
//         end: this.formatDate(new Date(today.getTime() - 24 * 60 * 60 * 1000)),
//       },
//       last7days: {
//         start: this.formatDate(
//           new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
//         ),
//         end: this.formatDate(today),
//       },
//       last30days: {
//         start: this.formatDate(
//           new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
//         ),
//         end: this.formatDate(today),
//       },
//       thisMonth: {
//         start: this.formatDate(
//           new Date(today.getFullYear(), today.getMonth(), 1)
//         ),
//         end: this.formatDate(today),
//       },
//       lastMonth: {
//         start: this.formatDate(
//           new Date(today.getFullYear(), today.getMonth() - 1, 1)
//         ),
//         end: this.formatDate(
//           new Date(today.getFullYear(), today.getMonth(), 0)
//         ),
//       },
//       thisYear: {
//         start: this.formatDate(new Date(today.getFullYear(), 0, 1)),
//         end: this.formatDate(today),
//       },
//     };

//     return ranges[period] || ranges.last30days;
//   },

//   /**
//    * Sanitize HTML to prevent XSS
//    */
//   sanitizeHTML(str) {
//     const temp = document.createElement("div");
//     temp.textContent = str;
//     return temp.innerHTML;
//   },

//   /**
//    * Copy text to clipboard
//    */
//   async copyToClipboard(text) {
//     try {
//       await navigator.clipboard.writeText(text);
//       this.showToast("Copied to clipboard!", "success");
//     } catch (err) {
//       console.error("Failed to copy:", err);
//       this.showToast("Failed to copy", "error");
//     }
//   },

//   /**
//    * Generate UUID
//    */
//   generateUUID() {
//     return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
//       /[xy]/g,
//       function (c) {
//         const r = (Math.random() * 16) | 0;
//         const v = c === "x" ? r : (r & 0x3) | 0x8;
//         return v.toString(16);
//       }
//     );
//   },

//   /**
//    * Parse query parameters from URL
//    */
//   getQueryParams() {
//     const params = {};
//     const queryString = window.location.search.slice(1);
//     const pairs = queryString.split("&");

//     pairs.forEach((pair) => {
//       const [key, value] = pair.split("=");
//       if (key) {
//         params[decodeURIComponent(key)] = decodeURIComponent(value || "");
//       }
//     });

//     return params;
//   },

//   /**
//    * Build table rows from data
//    */
//   buildTableRows(data, columns, actions = null) {
//     if (!data || data.length === 0) {
//       return `<tr><td colspan="${columns.length + (actions ? 1 : 0)}" class="px-6 py-8 text-center text-gray-500">No data available</td></tr>`;
//     }

//     return data
//       .map((row) => {
//         const cells = columns
//           .map((col) => {
//             let value = row[col.key];

//             // Apply formatter if provided
//             if (col.formatter) {
//               value = col.formatter(value, row);
//             }

//             return `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${value || "-"}</td>`;
//           })
//           .join("");

//         const actionCell = actions
//           ? `<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">${actions(row)}</td>`
//           : "";

//         return `<tr class="hover:bg-gray-50">${cells}${actionCell}</tr>`;
//       })
//       .join("");
//   },
// };

// // Export for use in other scripts
// if (typeof module !== "undefined" && module.exports) {
//   module.exports = Utils;
// }
