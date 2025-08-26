// Mobile Navigation Toggle
const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');

navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a link
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
    });
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background change on scroll
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.backdropFilter = 'blur(10px)';
    } else {
        navbar.style.background = '#fff';
        navbar.style.backdropFilter = 'none';
    }
});

// Animate elements on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all feature cards, pricing cards, and steps
document.addEventListener('DOMContentLoaded', () => {
    const elementsToAnimate = document.querySelectorAll('.feature-card, .pricing-card, .step');
    
    elementsToAnimate.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Contact form handling
const contactForm = document.querySelector('.contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const formData = new FormData(contactForm);
        const name = contactForm.querySelector('input[type="text"]').value;
        const email = contactForm.querySelector('input[type="email"]').value;
        const message = contactForm.querySelector('textarea').value;
        
        if (name && email && message) {
            // Show success message
            showNotification('Thank you for your inquiry! We will contact you at georgestraw022@gmail.com', 'success');
            contactForm.reset();
        } else {
            showNotification('Please fill in all fields.', 'error');
        }
    });
}

// Enhanced notification system for session expired and API errors
function showNotification(message, type, duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Create close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '×';
    closeButton.style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 18px;
        cursor: pointer;
        margin-left: 10px;
        padding: 0;
        opacity: 0.7;
        float: right;
    `;
    closeButton.onclick = () => dismissNotification(notification);
    
    // Create message container
    const messageContainer = document.createElement('div');
    messageContainer.style.display = 'flex';
    messageContainer.style.alignItems = 'center';
    messageContainer.style.justifyContent = 'space-between';
    
    const messageText = document.createElement('span');
    messageText.textContent = message;
    messageText.style.flex = '1';
    messageText.style.paddingRight = '10px';
    
    messageContainer.appendChild(messageText);
    messageContainer.appendChild(closeButton);
    notification.appendChild(messageContainer);
    
    // Enhanced styles with better colors and session error styling
    let backgroundColor = '#dc3545'; // Default error
    let borderColor = '#c82333';
    
    switch(type) {
        case 'success':
            backgroundColor = '#28a745';
            borderColor = '#1e7e34';
            break;
        case 'warning':
            backgroundColor = '#ffc107';
            borderColor = '#e0a800';
            break;
        case 'info':
            backgroundColor = '#17a2b8';
            borderColor = '#117a8b';
            break;
        case 'session-expired':
            backgroundColor = '#fd7e14'; // Orange for session issues
            borderColor = '#e55100';
            break;
        case 'error':
        default:
            backgroundColor = '#dc3545';
            borderColor = '#c82333';
    }
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        max-width: 400px;
        padding: 15px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        background: ${backgroundColor};
        border-left: 4px solid ${borderColor};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        line-height: 1.4;
    `;
    
    // Stack notifications if multiple exist
    const existingNotifications = document.querySelectorAll('.notification');
    const offset = existingNotifications.length * 80;
    notification.style.top = `${20 + offset}px`;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove after specified duration
    const autoRemoveTimeout = setTimeout(() => {
        dismissNotification(notification);
    }, duration);
    
    // Store timeout on element so it can be cancelled if manually dismissed
    notification._autoRemoveTimeout = autoRemoveTimeout;
}

// Function to dismiss notification
function dismissNotification(notification) {
    // Cancel auto-remove timeout if exists
    if (notification._autoRemoveTimeout) {
        clearTimeout(notification._autoRemoveTimeout);
    }
    
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
        // Reposition remaining notifications
        repositionNotifications();
    }, 300);
}

// Function to reposition remaining notifications after one is dismissed
function repositionNotifications() {
    const notifications = document.querySelectorAll('.notification');
    notifications.forEach((notification, index) => {
        notification.style.top = `${20 + index * 80}px`;
    });
}

// Handle session expired errors specifically
function handleSessionExpired(errorData, statusCode) {
    console.warn('Session expired or unauthorized access detected');
    
    let message = 'Your session has expired. Please reconnect your TikTok account.';
    if (errorData.error && errorData.error.includes('token')) {
        message = 'Your TikTok access token has expired. Please reconnect your account.';
    } else if (errorData.error && errorData.error.includes('refresh')) {
        message = 'Unable to refresh your session. Please reconnect your TikTok account.';
    }
    
    showNotification(message, 'session-expired', 8000); // Show for 8 seconds
    
    // Optionally redirect to reconnect after a delay
    setTimeout(() => {
        if (confirm('Your TikTok session has expired. Would you like to reconnect now?')) {
            window.location.href = '/auth/tiktok';
        }
    }, 2000);
}

// Handle general API errors
function handleApiError(statusCode, errorData, defaultMessage) {
    console.error(`API Error ${statusCode}:`, errorData);
    
    let message = defaultMessage;
    
    switch (statusCode) {
        case 429:
            message = 'Too many requests. Please wait a moment and try again.';
            break;
        case 503:
            message = 'TikTok service is temporarily unavailable. Please try again later.';
            break;
        case 500:
            message = 'Server error occurred. Please try again later.';
            break;
        default:
            if (errorData.error) {
                message = errorData.error;
            } else if (errorData.details) {
                message = errorData.details;
            }
    }
    
    showNotification(message, 'error');
}

// Modal functionality
function showModal(content) {
    const modalContainer = document.getElementById('modalContainer');
    modalContainer.innerHTML = content;
    modalContainer.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(event) {
    if (event.target === event.currentTarget || event.target.classList.contains('modal-close')) {
        const modalContainer = document.getElementById('modalContainer');
        modalContainer.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

function showInfoModal() {
    const content = `
        <div class="modal">
            <button class="modal-close" onclick="closeModal(event)">&times;</button>
            <h2>Postify Information</h2>
            <p>Postify is an educational resource about content automation concepts and best practices.</p>
            <h3>Key Features:</h3>
            <ul class="feature-list">
                <li><i class="fas fa-info-circle"></i> Content scheduling concepts</li>
                <li><i class="fas fa-info-circle"></i> Analytics and metrics understanding</li>
                <li><i class="fas fa-info-circle"></i> Team collaboration workflows</li>
                <li><i class="fas fa-info-circle"></i> Hashtag optimization strategies</li>
                <li><i class="fas fa-info-circle"></i> Content management best practices</li>
            </ul>
            <h3>Educational Purpose:</h3>
            <p>This platform provides information about automation tools and methodologies for educational purposes. It helps creators understand how automated systems can potentially improve content workflow efficiency.</p>
            <button class="btn btn-primary" onclick="closeModal(event)">Close</button>
        </div>
    `;
    showModal(content);
}

function showGuideModal() {
    const content = `
        <div class="modal">
            <button class="modal-close" onclick="closeModal(event)">&times;</button>
            <h2>TikTok Content Automation Guide</h2>
            <p>Learn about the concepts and best practices for content automation on TikTok.</p>
            <h3>Setup Guidelines:</h3>
            <ol style="text-align: left; padding-left: 20px;">
                <li><strong>Content Planning:</strong> Develop a content calendar and posting schedule</li>
                <li><strong>Quality Control:</strong> Ensure all content meets TikTok's community guidelines</li>
                <li><strong>Engagement Strategy:</strong> Plan for authentic audience interaction</li>
                <li><strong>Analytics Tracking:</strong> Monitor performance metrics and adjust strategy</li>
                <li><strong>Compliance:</strong> Stay updated with TikTok's terms of service</li>
            </ol>
            <h3>Best Practices:</h3>
            <ul class="feature-list">
                <li><i class="fas fa-lightbulb"></i> Maintain authentic engagement with your audience</li>
                <li><i class="fas fa-lightbulb"></i> Post consistently but not excessively</li>
                <li><i class="fas fa-lightbulb"></i> Use relevant and trending hashtags appropriately</li>
                <li><i class="fas fa-lightbulb"></i> Monitor content performance regularly</li>
                <li><i class="fas fa-lightbulb"></i> Follow TikTok's community guidelines strictly</li>
            </ul>
            <button class="btn btn-primary" onclick="closeModal(event)">Close</button>
        </div>
    `;
    showModal(content);
}

// Redirect to showInfoModal for backward compatibility
function showAPIModal() {
    showInfoModal();
}

// Button click effects
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        // Create ripple effect
        const ripple = document.createElement('span');
        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        btn.style.position = 'relative';
        btn.style.overflow = 'hidden';
        btn.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    });
});

// Add ripple animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Counter animation for pricing
function animateCounter(element, target, duration = 1000) {
    let start = 0;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
        start += increment;
        element.textContent = Math.floor(start);
        
        if (start >= target) {
            element.textContent = target;
            clearInterval(timer);
        }
    }, 16);
}

// Lazy loading for images (if any are added later)
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Typing effect for hero title
function typeWriter(element, text, speed = 50) {
    let i = 0;
    element.innerHTML = '';
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Initialize typing effect when page loads
document.addEventListener('DOMContentLoaded', () => {
    const heroTitle = document.querySelector('.hero h1');
    if (heroTitle) {
        const originalText = heroTitle.textContent;
        typeWriter(heroTitle, originalText, 100);
    }
});