// SkillScout - Main JavaScript File

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initFlashMessages();
    initFormValidation();
    initProfileForm();
    initSmoothScrolling();
    initTooltips();
    initLoadingStates();
});

// Flash Messages Management
function initFlashMessages() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert.classList.contains('alert-dismissible')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Add click to dismiss functionality
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-close')) {
            const alert = e.target.closest('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }
    });
}

// Form Validation
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                showValidationErrors(form);
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Password confirmation validation
    const password = form.querySelector('input[name="password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        isValid = false;
        confirmPassword.classList.add('is-invalid');
        showError(confirmPassword, 'Passwords do not match');
    }
    
    // Email validation
    const email = form.querySelector('input[type="email"]');
    if (email && email.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.value)) {
            isValid = false;
            email.classList.add('is-invalid');
            showError(email, 'Please enter a valid email address');
        }
    }
    
    return isValid;
}

function showValidationErrors(form) {
    const invalidFields = form.querySelectorAll('.is-invalid');
    if (invalidFields.length > 0) {
        showFlashMessage('Please correct the errors in the form.', 'danger');
        invalidFields[0].focus();
    }
}

function showError(field, message) {
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

// Profile Form Toggle
function initProfileForm() {
    const cgpaRadio = document.getElementById('cgpa');
    const percentageRadio = document.getElementById('percentage');
    const cgpaInput = document.getElementById('cgpa-input');
    const percentageInput = document.getElementById('percentage-input');

    if (cgpaRadio && percentageRadio && cgpaInput && percentageInput) {
        function toggleInputs() {
            if (cgpaRadio.checked) {
                cgpaInput.style.display = 'block';
                percentageInput.style.display = 'none';
                cgpaInput.querySelector('input').required = true;
                percentageInput.querySelector('input').required = false;
            } else {
                cgpaInput.style.display = 'none';
                percentageInput.style.display = 'block';
                cgpaInput.querySelector('input').required = false;
                percentageInput.querySelector('input').required = true;
            }
        }

        cgpaRadio.addEventListener('change', toggleInputs);
        percentageRadio.addEventListener('change', toggleInputs);

        // Initial toggle based on saved preference
        toggleInputs();
    }
}

// Smooth Scrolling
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Loading States
function initLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loading"></span> Processing...';
            }
        });
    });
}

// Flash Message Utility
function showFlashMessage(message, type = 'info') {
    const flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    flashContainer.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }
    }, 5000);
}

// Progress Bar Animation
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}

// Card Hover Effects
function initCardHoverEffects() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Form Auto-save (for profile form)
function initFormAutoSave() {
    const profileForm = document.querySelector('form[action*="profile"]');
    if (!profileForm) return;
    
    const formData = new FormData(profileForm);
    const inputs = profileForm.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('change', function() {
            // Save to localStorage
            const formData = new FormData(profileForm);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            localStorage.setItem('profileFormData', JSON.stringify(data));
        });
    });
    
    // Restore data on page load
    const savedData = localStorage.getItem('profileFormData');
    if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach(key => {
            const input = profileForm.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = data[key];
            }
        });
    }
}

// Responsive Navigation
function initResponsiveNav() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking on a link
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                    bsCollapse.hide();
                }
            });
        });
    }
}

// Search Functionality (if needed)
function initSearch() {
    const searchInput = document.querySelector('#search-input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const searchableElements = document.querySelectorAll('[data-searchable]');
        
        searchableElements.forEach(element => {
            const text = element.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                element.style.display = '';
            } else {
                element.style.display = 'none';
            }
        });
    });
}

// Accessibility Improvements
function initAccessibility() {
    // Add skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'sr-only sr-only-focusable';
    skipLink.textContent = 'Skip to main content';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        z-index: 1001;
        color: white;
        background: #000;
        padding: 8px 16px;
        text-decoration: none;
    `;
    
    skipLink.addEventListener('focus', function() {
        this.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content id
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.id = 'main-content';
    }
}

// Performance Optimization
function initPerformanceOptimizations() {
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
    
    // Debounce search input
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
    
    // Apply debouncing to search
    const searchInput = document.querySelector('#search-input');
    if (searchInput) {
        const debouncedSearch = debounce(initSearch, 300);
        searchInput.addEventListener('input', debouncedSearch);
    }
}

// Initialize all features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initFlashMessages();
    initFormValidation();
    initProfileForm();
    initSmoothScrolling();
    initTooltips();
    initLoadingStates();
    initCardHoverEffects();
    initFormAutoSave();
    initResponsiveNav();
    initSearch();
    initAccessibility();
    initPerformanceOptimizations();
    
    // Animate progress bars after a short delay
    setTimeout(animateProgressBars, 500);
});

// Export functions for global use
window.SkillScout = {
    showFlashMessage,
    animateProgressBars,
    validateForm
};
