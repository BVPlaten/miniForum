// miniForum - Minimal JavaScript für ressourcenschonende Foren
// Nur essenzielle Funktionen, kein Framework

document.addEventListener('DOMContentLoaded', function() {
    // Unread message count updater (for real-time notifications)
    function updateUnreadCount() {
        if (typeof current_user !== 'undefined' && current_user) {
            fetch('/messages/unread_count')
                .then(response => response.json())
                .then(data => {
                    const badge = document.querySelector('.unread-badge');
                    if (badge) {
                        if (data.unread_count > 0) {
                            badge.textContent = data.unread_count;
                            badge.style.display = 'flex';
                        } else {
                            badge.style.display = 'none';
                        }
                    }
                })
                .catch(error => console.log('Could not update unread count:', error));
        }
    }

    // Update unread count every 30 seconds
    setInterval(updateUnreadCount, 30000);

    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.max(this.scrollHeight, 100) + 'px';
        });
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Möchten Sie diesen Eintrag wirklich löschen?')) {
                e.preventDefault();
            }
        });
    });

    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Bitte füllen Sie alle Pflichtfelder aus.');
            }
        });
    });

    // Auto-save draft for long forms (every 30 seconds)
    const longForms = document.querySelectorAll('form textarea');
    longForms.forEach(form => {
        const textarea = form.querySelector('textarea');
        if (textarea && textarea.getAttribute('rows') > 5) {
            const formKey = 'draft_' + window.location.pathname;
            
            // Load saved draft
            const savedDraft = localStorage.getItem(formKey);
            if (savedDraft) {
                textarea.value = savedDraft;
            }
            
            // Save draft periodically
            setInterval(() => {
                if (textarea.value.trim()) {
                    localStorage.setItem(formKey, textarea.value);
                }
            }, 30000);
            
            // Clear draft on successful submit
            form.addEventListener('submit', () => {
                localStorage.removeItem(formKey);
            });
        }
    });

    // Responsive navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('nav-menu-active');
        });
    }

    // Click outside to close mobile menu
    document.addEventListener('click', function(e) {
        if (navMenu && navToggle && !navMenu.contains(e.target) && !navToggle.contains(e.target)) {
            navMenu.classList.remove('nav-menu-active');
        }
    });

    // Print-friendly styles
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Copy code blocks functionality
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const button = document.createElement('button');
        button.className = 'btn-copy';
        button.textContent = 'Kopieren';
        button.style.cssText = 'position: absolute; top: 5px; right: 5px; padding: 2px 8px; font-size: 12px;';
        
        const pre = block.parentElement;
        pre.style.position = 'relative';
        pre.appendChild(button);
        
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent).then(() => {
                button.textContent = 'Kopiert!';
                setTimeout(() => {
                    button.textContent = 'Kopieren';
                }, 2000);
            });
        });
    });

    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));

    // Performance monitoring
    if ('performance' in window) {
        window.addEventListener('load', function() {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            console.log('Page load time:', loadTime + 'ms');
            
            if (loadTime > 2000) {
                console.warn('Slow page load detected');
            }
        });
    }

    // Service Worker registration (for offline support)
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(error => {
            console.log('Service Worker registration failed:', error);
        });
    }
});

// Utility functions
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
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export for use in other scripts
window.miniForum = {
    updateUnreadCount,
    debounce,
    throttle
};