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

// Notification system
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        ${type === 'success' ? 'background: #28a745;' : 'background: #dc3545;'}
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
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