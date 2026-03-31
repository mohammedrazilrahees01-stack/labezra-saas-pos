/**
 * POS Logic — Labezra POS SaaS
 * Single source of truth for all POS JS interactions.
 * CSRF_TOKEN is injected by the template as a global var before this script loads.
 */

"use strict";

// ══════════════════════════════════════════════════════
// ADD PRODUCT TO CART (AJAX)
// ══════════════════════════════════════════════════════
function addProduct(productId) {
  // Visual feedback — dim the card while adding
  const card = document.querySelector(`[onclick="addProduct('${productId}')"]`);
  if (card) {
    card.classList.add("adding");
    card.style.pointerEvents = "none";
  }

  const formData = new FormData();
  formData.append("product_id", productId);

  fetch("/pos/add-to-cart/", {
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
      "X-Requested-With": "XMLHttpRequest",
    },
    body: formData,
  })
    .then((res) => {
      if (res.ok) {
        // Reload to update cart counts, subtotals etc.
        window.location.href =
          window.location.pathname + window.location.search;
      } else {
        console.error("Server rejected add-to-cart.");
        location.reload();
      }
    })
    .catch((err) => {
      console.error("Fetch error:", err);
      location.reload();
    });
}

// ══════════════════════════════════════════════════════
// PRODUCT SEARCH FILTER (live, debounced)
// FIX: was searching ".p-name" – template now uses .p-name consistently
// ══════════════════════════════════════════════════════
const searchInput = document.getElementById("productSearch");
let searchTimeout;

if (searchInput) {
  // Auto-focus for faster billing
  searchInput.focus();

  searchInput.addEventListener("input", function () {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      const query = this.value.toLowerCase().trim();
      document.querySelectorAll(".product-item").forEach((item) => {
        // FIX: selector is .p-name (matches template class)
        const nameEl = item.querySelector(".p-name");
        if (!nameEl) return;
        const match = nameEl.innerText.toLowerCase().includes(query);
        item.style.display = match ? "" : "none";
      });
    }, 150);
  });
}

// ══════════════════════════════════════════════════════
// PAYMENT METHOD — SHOW/HIDE CASH INPUT
// FIX: adds id="cashReceived" input toggle based on payment type
// ══════════════════════════════════════════════════════
const paymentSelect = document.getElementById("paymentMethod");
const cashInput = document.getElementById("cashReceived"); // FIX: id added to template

function syncCashInput() {
  if (!paymentSelect || !cashInput) return;
  const isCash = paymentSelect.value === "CASH";
  cashInput.style.display = isCash ? "block" : "none";
  cashInput.required = isCash;
  if (!isCash) cashInput.value = "";
}

if (paymentSelect) {
  paymentSelect.addEventListener("change", syncCashInput);
  // Set initial state on page load
  syncCashInput();
}

// ══════════════════════════════════════════════════════
// QTY BUTTONS — prevent double-submit
// ══════════════════════════════════════════════════════
document.querySelectorAll(".qty-btn").forEach((btn) => {
  btn.addEventListener("click", function () {
    this.disabled = true;
    this.style.opacity = "0.5";
    this.closest("form").submit();
  });
});

// ══════════════════════════════════════════════════════
// CHECKOUT FORM — CLIENT-SIDE CASH VALIDATION
// FIX: was referencing wrong selectors (.total-value was missing, cashReceived id was missing)
// ══════════════════════════════════════════════════════
const checkoutForm = document.getElementById("checkoutForm");

if (checkoutForm) {
  checkoutForm.addEventListener("submit", function (e) {
    // Only validate cash payments
    if (!paymentSelect || paymentSelect.value !== "CASH") return;

    const totalEl = document.querySelector(".total-value"); // FIX: class exists in template
    if (!totalEl || !cashInput) return;

    // Strip non-numeric characters (e.g. "AED ")
    const grandTotal = parseFloat(totalEl.innerText.replace(/[^0-9.]/g, ""));
    const received = parseFloat(cashInput.value || "0");

    if (isNaN(grandTotal)) return; // Empty cart — let server handle

    if (received < grandTotal) {
      e.preventDefault();
      showToast(
        `Cash received (AED ${received.toFixed(2)}) is less than total (AED ${grandTotal.toFixed(2)}).`,
        "error"
      );
      cashInput.focus();
      cashInput.classList.add("input-error");
    }
  });

  // Clear error highlight when user fixes the value
  if (cashInput) {
    cashInput.addEventListener("input", () => {
      cashInput.classList.remove("input-error");
    });
  }
}

// ══════════════════════════════════════════════════════
// TOAST NOTIFICATIONS (lightweight, no library needed)
// ══════════════════════════════════════════════════════
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `pos-toast pos-toast--${type}`;
  toast.innerHTML = `<i class="ri-${type === "error" ? "error-warning" : "information"}-line"></i> ${message}`;
  document.body.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => toast.classList.add("visible"));

  // Auto-remove after 3 s
  setTimeout(() => {
    toast.classList.remove("visible");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ══════════════════════════════════════════════════════
// AUTO-DISMISS FLASH MESSAGES (after 4 s)
// ══════════════════════════════════════════════════════
window.addEventListener("DOMContentLoaded", () => {
  const flashBox = document.getElementById("pos-messages");
  if (flashBox) {
    setTimeout(() => {
      flashBox.style.opacity = "0";
      flashBox.style.transition = "opacity .4s";
      setTimeout(() => flashBox.remove(), 400);
    }, 4000);
  }
});
