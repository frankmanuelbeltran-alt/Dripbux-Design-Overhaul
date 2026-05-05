/**
 * DripBux Premium - Main JavaScript
 * ================================
 * Interactions, cart functionality, and animations
 */

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
    initNavbar();
    initMobileMenu();
    initFlashMessages();
    initSearch();
    initScrollAnimations();
});

// =============================================================================
// NAVBAR
// =============================================================================

function initNavbar() {
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        // Add shadow on scroll
        if (currentScroll > 50) {
            navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.3)';
        } else {
            navbar.style.boxShadow = 'none';
        }
        
        lastScroll = currentScroll;
    });
}

// =============================================================================
// MOBILE MENU
// =============================================================================

function initMobileMenu() {
    const toggle = document.getElementById('mobileMenuToggle');
    const menu = document.getElementById('mobileMenu');
    const close = document.getElementById('mobileMenuClose');
    
    if (toggle && menu) {
        toggle.addEventListener('click', function() {
            menu.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }
    
    if (close && menu) {
        close.addEventListener('click', function() {
            menu.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    // Close on backdrop click
    if (menu) {
        menu.addEventListener('click', function(e) {
            if (e.target === menu) {
                menu.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
}

// =============================================================================
// FLASH MESSAGES
// =============================================================================

function initFlashMessages() {
    const messages = document.querySelectorAll('.flash-message[data-auto-dismiss]');
    
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transform = 'translateX(100%)';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
}

// =============================================================================
// SEARCH
// =============================================================================

function initSearch() {
    const searchInput = document.querySelector('.search-input-wrapper input');
    const searchResults = document.getElementById('searchResults');
    let debounceTimer;
    
    if (searchInput && searchResults) {
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();
            
            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.classList.remove('active');
                return;
            }
            
            debounceTimer = setTimeout(function() {
                fetchSearchResults(query);
            }, 300);
        });
        
        // Close search results on click outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-input-wrapper')) {
                searchResults.innerHTML = '';
                searchResults.classList.remove('active');
            }
        });
    }
}

function fetchSearchResults(query) {
    const searchResults = document.getElementById('searchResults');
    
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.products && data.products.length > 0) {
                renderSearchResults(data.products);
            } else {
                searchResults.innerHTML = '<div class="search-no-results">No products found</div>';
                searchResults.classList.add('active');
            }
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

function renderSearchResults(products) {
    const searchResults = document.getElementById('searchResults');
    
    const html = products.map(product => `
        <a href="/shop/product/${product.slug}" class="search-result-item">
            <div class="search-result-image">
                ${product.image ? `<img src="/static/images/products/${product.image}" alt="${product.name}">` : '<i data-lucide="box"></i>'}
            </div>
            <div class="search-result-info">
                <span class="search-result-name">${product.name}</span>
                <span class="search-result-category">${product.category || 'Product'}</span>
            </div>
            <span class="search-result-price">${product.price.toLocaleString()} <i data-lucide="coins"></i></span>
        </a>
    `).join('');
    
    searchResults.innerHTML = html;
    searchResults.classList.add('active');
    lucide.createIcons();
}

// =============================================================================
// CART FUNCTIONS
// =============================================================================

function updateCartBadge(count) {
    const badge = document.getElementById('cartBadge');
    if (badge) {
        badge.textContent = count;
        badge.setAttribute('data-count', count);
        
        // Animate badge
        badge.style.transform = 'scale(1.3)';
        setTimeout(() => {
            badge.style.transform = 'scale(1)';
        }, 200);
    }
}

function quickAddToCart(productId) {
    // Show size selector modal or redirect to product page
    window.location.href = `/shop/product/${productId}`;
}

function toggleWishlist(productId) {
    const btn = document.querySelector(`.wishlist-btn[data-product-id="${productId}"]`);
    const isInWishlist = btn && btn.classList.contains('active');
    
    const url = isInWishlist ? `/shop/wishlist/remove/${productId}` : `/shop/wishlist/add/${productId}`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (btn) {
                btn.classList.toggle('active');
            }
            showNotification(data.message, 'success');
        } else {
            if (data.message.includes('sign in')) {
                window.location.href = '/auth/login';
            } else {
                showNotification(data.message, 'error');
            }
        }
    })
    .catch(error => {
        console.error('Wishlist error:', error);
    });
}

// =============================================================================
// NOTIFICATIONS
// =============================================================================

function showNotification(message, type = 'info') {
    // Use new toast system if available
    if (window.DripBuxToast) {
        window.DripBuxToast.show(message, type);
        return;
    }

    // Fallback to legacy notification
    const container = document.getElementById('flashMessages') || createNotificationContainer();

    const icons = {
        success: 'check-circle',
        error: 'alert-circle',
        warning: 'alert-triangle',
        info: 'info'
    };

    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type}`;
    notification.innerHTML = `
        <i data-lucide="${icons[type]}"></i>
        <span>${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">
            <i data-lucide="x"></i>
        </button>
    `;

    container.appendChild(notification);
    lucide.createIcons();

    // Auto dismiss
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'flashMessages';
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// =============================================================================
// UTILITIES
// =============================================================================

function getCsrfToken() {
    const token = document.querySelector('input[name="csrf_token"]');
    return token ? token.value : '';
}

function formatRobux(amount) {
    return amount.toLocaleString();
}

// =============================================================================
// SCROLL ANIMATIONS
// =============================================================================

function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.product-card, .feature-card, .stat-card').forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
}

// =============================================================================
// LOADING OVERLAY
// =============================================================================

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// =============================================================================
// FORM VALIDATION
// =============================================================================

function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('error');
            
            // Add error message if not exists
            let errorMsg = input.parentElement.querySelector('.form-error');
            if (!errorMsg) {
                errorMsg = document.createElement('span');
                errorMsg.className = 'form-error';
                errorMsg.textContent = 'This field is required';
                input.parentElement.appendChild(errorMsg);
            }
        } else {
            input.classList.remove('error');
            const errorMsg = input.parentElement.querySelector('.form-error');
            if (errorMsg) {
                errorMsg.remove();
            }
        }
    });
    
    return isValid;
}

// =============================================================================
// QUANTITY SELECTOR
// =============================================================================

function initQuantitySelector(container) {
    const input = container.querySelector('.qty-input');
    const minusBtn = container.querySelector('.qty-btn:first-child');
    const plusBtn = container.querySelector('.qty-btn:last-child');
    
    if (minusBtn) {
        minusBtn.addEventListener('click', () => {
            let value = parseInt(input.value) || 1;
            if (value > 1) {
                input.value = value - 1;
                input.dispatchEvent(new Event('change'));
            }
        });
    }
    
    if (plusBtn) {
        plusBtn.addEventListener('click', () => {
            let value = parseInt(input.value) || 1;
            const max = parseInt(input.max) || 99;
            if (value < max) {
                input.value = value + 1;
                input.dispatchEvent(new Event('change'));
            }
        });
    }
}

// Initialize quantity selectors
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.quantity-selector').forEach(initQuantitySelector);
});

// =============================================================================
// ACCORDION
// =============================================================================

function toggleAccordion(header) {
    const item = header.parentElement;
    const content = item.querySelector('.accordion-content');
    const isActive = item.classList.contains('active');
    
    // Close all accordions in the same group
    const group = item.parentElement;
    group.querySelectorAll('.accordion-item').forEach(acc => {
        acc.classList.remove('active');
        acc.querySelector('.accordion-content').style.maxHeight = null;
    });
    
    // Open clicked accordion if it was closed
    if (!isActive) {
        item.classList.add('active');
        content.style.maxHeight = content.scrollHeight + 'px';
    }
}

// Initialize accordions
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.accordion-item.active .accordion-content').forEach(content => {
        content.style.maxHeight = content.scrollHeight + 'px';
    });
});

// =============================================================================
// IMAGE LAZY LOADING
// =============================================================================

if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    });
}

// =============================================================================
// SMOOTH SCROLL
// =============================================================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const target = document.querySelector(targetId);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// =============================================================================
// KEYBOARD NAVIGATION
// =============================================================================

document.addEventListener('keydown', function(e) {
    // ESC to close mobile menu
    if (e.key === 'Escape') {
        const mobileMenu = document.getElementById('mobileMenu');
        if (mobileMenu && mobileMenu.classList.contains('active')) {
            mobileMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        // Close search results
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.innerHTML = '';
            searchResults.classList.remove('active');
        }
    }
});

// =============================================================================
// PERFORMANCE: Debounce and Throttle
// =============================================================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// =============================================================================
// EXPORT FUNCTIONS FOR GLOBAL ACCESS
// =============================================================================

window.DripBux = {
    updateCartBadge,
    toggleWishlist,
    showNotification,
    showLoading,
    hideLoading,
    formatRobux,
    getCsrfToken
};
