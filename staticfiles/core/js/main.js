// Main JavaScript file for the application

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const messages = document.querySelectorAll('.alert');
    if (messages.length > 0) {
        setTimeout(() => {
            messages.forEach(message => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            });
        }, 5000);
    }

    // Mobile menu toggle functionality
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuToggle && navLinks) {
        mobileMenuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            const isExpanded = mobileMenuToggle.getAttribute('aria-expanded') === 'true' || false;
            mobileMenuToggle.setAttribute('aria-expanded', !isExpanded);
            mobileMenuToggle.setAttribute('aria-label', isExpanded ? 'Abrir menú' : 'Cerrar menú');
            mobileMenuToggle.innerHTML = isExpanded ? 
                '<i class="fas fa-bars"></i>' : 
                '<i class="fas fa-times"></i>';
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.navbar') && navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                mobileMenuToggle.setAttribute('aria-label', 'Abrir menú');
                mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
        
        // Close menu when a nav link is clicked (for mobile)
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 992) {
                    navLinks.classList.remove('active');
                    mobileMenuToggle.setAttribute('aria-expanded', 'false');
                    mobileMenuToggle.setAttribute('aria-label', 'Abrir menú');
                    mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
                }
            });
        });
    }

    // Add active class to current navigation link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        // Check if the link's href matches the current path
        // or if the current path starts with the link's href (for nested routes)
        const linkPath = link.getAttribute('href');
        if (linkPath === currentPath || 
            (linkPath !== '/' && currentPath.startsWith(linkPath) && linkPath !== '#')) {
            link.classList.add('active');
            // Also highlight parent nav items in case of dropdowns
            const parentNavItem = link.closest('.nav-item');
            if (parentNavItem) {
                parentNavItem.classList.add('active');
            }
        }
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Adjust for fixed header
                    behavior: 'smooth'
                });
            }
        });
    });

    // Confirm before performing destructive actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            if (!confirm(button.dataset.confirm || '¿Está seguro de que desea realizar esta acción?')) {
                e.preventDefault();
            }
        });
    });

    // Add loading state to buttons with loading class
    document.querySelectorAll('.btn-loading').forEach(button => {
        button.addEventListener('click', function() {
            this.classList.add('loading');
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            
            // Revert after form submission or AJAX completion
            const form = this.closest('form');
            if (form) {
                form.addEventListener('submit', function resetButton() {
                    button.classList.remove('loading');
                    button.disabled = false;
                    button.innerHTML = originalText;
                    form.removeEventListener('submit', resetButton);
                });
            } else {
                // For non-form buttons, revert after 3 seconds
                setTimeout(() => {
                    button.classList.remove('loading');
                    button.disabled = false;
                    button.innerHTML = originalText;
                }, 3000);
            }
        });
    });
});

// Add a small delay before removing the loading class from the body
// to prevent FOUC (Flash of Unstyled Content)
window.addEventListener('load', function() {
    document.body.classList.add('loaded');
});
