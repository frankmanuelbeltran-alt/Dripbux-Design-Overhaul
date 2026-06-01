/**
 * DripBux Main JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Toast notification helper
    window.showToast = function(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const iconName = type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info';
        toast.innerHTML = `
            <i data-lucide="${iconName}" width="18" height="18"></i>
            <span>${message}</span>
        `;
        container.appendChild(toast);
        lucide.createIcons({ nodes: [toast] });

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    };

    // Theme toggle and navbar scroll effect
    const navbar = document.getElementById('mainNavbar');
    const themeToggle = document.getElementById('themeToggleBtn');
    const themeToggleIcon = document.getElementById('themeToggleIcon');

    function setTheme(theme) {
        if (theme === 'light') {
            document.body.classList.add('light-theme');
            document.body.classList.remove('dark-theme');
            if (themeToggleIcon) themeToggleIcon.setAttribute('data-lucide', 'sun');
        } else {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
            if (themeToggleIcon) themeToggleIcon.setAttribute('data-lucide', 'moon');
        }
        if (navbar) {
            const currentScroll = window.pageYOffset;
            const navBg = getComputedStyle(document.body).getPropertyValue(currentScroll > 100 ? '--nav-bg-scrolled' : '--nav-bg').trim();
            navbar.style.background = navBg;
        }
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        localStorage.setItem('dripbuxTheme', theme);
    }

    function loadTheme() {
        const storedTheme = localStorage.getItem('dripbuxTheme');
        if (storedTheme === 'light' || storedTheme === 'dark') {
            setTheme(storedTheme);
        } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            setTheme('dark');
        } else {
            setTheme('light');
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const nextTheme = document.body.classList.contains('light-theme') ? 'dark' : 'light';
            setTheme(nextTheme);
        });
    }

    loadTheme();

    if (navbar) {
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            const navBg = getComputedStyle(document.body).getPropertyValue('--nav-bg').trim();
            const navBgScrolled = getComputedStyle(document.body).getPropertyValue('--nav-bg-scrolled').trim();
            if (currentScroll > 100) {
                navbar.style.background = navBgScrolled;
                navbar.style.backdropFilter = 'blur(20px)';
            } else {
                navbar.style.background = navBg;
            }
            lastScroll = currentScroll;
        });
    }

    // Cart AJAX helper
    window.addToCart = function(productId, sizeId, quantity = 1) {
        const formData = new FormData();
        formData.append('product_id', productId);
        if (sizeId) formData.append('size_id', sizeId);
        formData.append('quantity', quantity);

        fetch('/cart/add', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const badge = document.getElementById('cartBadge');
                if (badge) badge.textContent = data.cart_count;
                showToast(data.message, 'success');
            } else {
                showToast(data.message, 'error');
            }
        })
        .catch(() => showToast('Error adding to cart', 'error'));
    };

    window.buyNowProduct = function(productId) {
        const quantityInput = document.getElementById('productQuantityInput');
        const quantity = quantityInput ? parseInt(quantityInput.value, 10) || 1 : 1;
        const formData = new FormData();
        formData.append('product_id', productId);
        formData.append('quantity', quantity);

        fetch('/cart/add?checkout=1', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                if (data.redirect) {
                    window.location.href = data.redirect;
                    return;
                }
                const badge = document.getElementById('cartBadge');
                if (badge) badge.textContent = data.cart_count;
                showToast(data.message, 'success');
            } else {
                showToast(data.message, 'error');
            }
        })
        .catch(() => showToast('Error processing checkout', 'error'));
    };

    // Intercept add-to-cart form submission and send via AJAX
    document.querySelectorAll('.add-cart-form').forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault();
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    const badge = document.getElementById('cartBadge');
                    if (badge) badge.textContent = data.cart_count;
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message, 'error');
                }
            })
            .catch(() => showToast('Error adding to cart', 'error'));
        });
    });

    // Wishlist toggle
    window.toggleWishlist = function(productId, button) {
        const isInWishlist = button.classList.contains('in-wishlist');
        const url = isInWishlist ? `/shop/wishlist/remove/${productId}` : `/shop/wishlist/add/${productId}`;
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => {
            return response.json().then(data => {
                if (!response.ok) {
                    throw new Error(data.message || 'Error updating wishlist');
                }
                return data;
            });
        })
        .then(data => {
            if (data.success) {
                // Toggle local state
                button.classList.toggle('in-wishlist');
                const icon = button.querySelector('i');
                if (icon) {
                    icon.setAttribute('data-lucide', 'heart');
                    lucide.createIcons({ nodes: [button] });
                }

                // Update navbar badge
                const wishlistCount = document.getElementById('navWishlistCount');
                if (wishlistCount && data.wishlist_count !== undefined) {
                    wishlistCount.textContent = data.wishlist_count;
                }

                // If we're on the wishlist page and this was a remove action, remove the product card
                if (document.body.querySelector('.wishlist-page') && isInWishlist) {
                    const card = button.closest('.product-card');
                    if (card) {
                        card.remove();
                        const remaining = document.querySelectorAll('.products-grid .product-card').length;
                        if (remaining === 0) {
                            // reload to show empty state rendered by server
                            location.reload();
                        }
                    }
                }

                showToast(data.message, 'success');
            } else {
                showToast(data.message || 'Error updating wishlist', 'error');
            }
        })
        .catch(error => {
            showToast(error.message || 'Error updating wishlist', 'error');
        });
    };

    // Counter animation for stats
    document.querySelectorAll('[data-count]').forEach(el => {
        const target = parseInt(el.dataset.count);
        const duration = 2000;
        const start = performance.now();

        function update(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.floor(target * easeOut).toLocaleString();
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    });

    // Lazy load images
    document.querySelectorAll('img[data-src]').forEach(img => {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
    });

    // Copy to clipboard
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!', 'success');
        });
    };

    // Password visibility toggle
    document.querySelectorAll('.password-toggle-btn').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const wrapper = toggle.closest('.password-input-group');
            const input = wrapper ? wrapper.querySelector('input') : null;
            if (!input) return;
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            const icon = toggle.querySelector('i');
            if (icon) {
                icon.setAttribute('data-lucide', isPassword ? 'eye' : 'eye-off');
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons({ nodes: [toggle] });
                }
            }
            toggle.classList.add('toggle-animate');
            window.setTimeout(() => toggle.classList.remove('toggle-animate'), 160);
        });
    });
});
