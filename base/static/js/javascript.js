

// Banner javascript 
window.addEventListener('DOMContentLoaded', function() {
  const bannerSlides = document.querySelectorAll('.banner-slide');
  const bannerPrev = document.querySelector('.banner-prev');
  const bannerNext = document.querySelector('.banner-next');
  const bannerDotsContainer = document.getElementById('banner-slide-dots');
  
  // Exit silently if banner elements don't exist
  if (!bannerSlides.length || !bannerDotsContainer) {
    return; // Removed console.warn
  }
  
  let bannerIndex = 0, bannerTimer = null;

  // Create navigation dots
  bannerSlides.forEach((s, i) => {
    const dot = document.createElement('span');
    dot.className = 'banner-slide-dot';
    if (i === 0) dot.classList.add('active');
    dot.onclick = () => showSlide(i);
    bannerDotsContainer.appendChild(dot);
  });
  const bannerDots = document.querySelectorAll('.banner-slide-dot');

  function showSlide(n) {
    if (n === bannerIndex) return;
    bannerSlides[bannerIndex].classList.remove('active');
    bannerDots[bannerIndex].classList.remove('active');
    bannerIndex = n;
    bannerSlides[bannerIndex].classList.add('active');
    bannerDots[bannerIndex].classList.add('active');
    resetTimer();
  }
  
  function nextSlide() { 
    showSlide((bannerIndex + 1) % bannerSlides.length); 
  }
  
  function prevSlide() { 
    showSlide((bannerIndex - 1 + bannerSlides.length) % bannerSlides.length); 
  }
  
  function resetTimer() {
    if(bannerTimer) clearInterval(bannerTimer);
    bannerTimer = setInterval(nextSlide, 2200);
  }
  
  // Only add event listeners if buttons exist
  if (bannerPrev) bannerPrev.onclick = prevSlide;
  if (bannerNext) bannerNext.onclick = nextSlide;
  
  resetTimer();
});

// Modal Javascript
(function() {
  const modal = document.getElementById('couponModal');
  const openBtn = document.getElementById('openCouponModalBtn');
  const form = document.getElementById('couponForm');
  const codeInput = document.getElementById('couponCode');
  const message = document.getElementById('couponMessage');

  // Exit silently if modal doesn't exist
  if (!modal) {
    return; // Removed console.warn
  }

  // Fixed test code (case-insensitive)
  const TEST_CODE = 'TEST2025';
  let closing = false;

  function openModal() {
    if (!modal) return;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    setTimeout(() => codeInput && codeInput.focus(), 50);
    document.addEventListener('keydown', onKeydown);
  }

  function closeModal() {
    if (!modal || closing) return;
    closing = true;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.removeEventListener('keydown', onKeydown);
    if (message) {
      message.textContent = '';
      message.classList.remove('coupon-form__message--success', 'coupon-form__message--error');
    }
    if (form) form.reset();
    setTimeout(() => { closing = false; }, 120);
  }

  function onKeydown(e) {
    if (e.key === 'Escape') closeModal();
  }

  // Open trigger
  if (openBtn) {
    openBtn.addEventListener('click', openModal);
    openBtn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openModal();
      }
    });
  }

  // Close on backdrop and elements marked data-close="true"
  if (modal) {
    modal.addEventListener('pointerdown', (e) => {
      if (e.target && e.target.dataset && e.target.dataset.close === 'true') {
        e.preventDefault();
        closeModal();
      }
    });
    modal.addEventListener('click', (e) => {
      if (e.target && e.target.dataset && e.target.dataset.close === 'true') {
        closeModal();
      }
    });
  }

  // Form submit: just check fixed code and show messages
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const raw = codeInput ? codeInput.value : '';
      const code = (raw || '').trim();

      if (!message) return;

      message.textContent = '';
      message.classList.remove('coupon-form__message--success', 'coupon-form__message--error');

      if (!code) {
        message.textContent = 'Please enter a coupon code.';
        message.classList.add('coupon-form__message--error');
        if (codeInput) codeInput.focus();
        return;
      }

      if (code.toUpperCase() === TEST_CODE) {
        message.textContent = 'Coupon applied successfully!';
        message.classList.add('coupon-form__message--success');
        setTimeout(closeModal, 900);
      } else {
        message.textContent = 'Invalid coupon code. Please try again.';
        message.classList.add('coupon-form__message--error');
      }
    });
  }
})();

// ========================================
// UNIFIED CAROUSEL SCRIPT
// No cloning, no duplicates, clean implementation
// ========================================

function smoothScrollCarousel(carouselId, direction) {
  const carousel = document.getElementById(carouselId);
  if (!carousel) return; // Exit silently
  
  // Find a card to measure width
  const card = carousel.querySelector('.course-card');
  if (!card) return; // Exit silently
  
  const cardWidth = card.offsetWidth;
  const gap = 18; // Gap between cards
  const scrollAmount = (cardWidth + gap) * 2; // Scroll 2 cards at a time
  
  const scrollLeft = direction === 'left' ? -scrollAmount : scrollAmount;
  
  carousel.scrollBy({
    left: scrollLeft,
    behavior: 'smooth'
  });
}

// Update arrow states based on scroll position
function updateCarouselArrows(carouselId) {
  const carousel = document.getElementById(carouselId);
  if (!carousel) return;
  
  const container = carousel.closest('.scroll-row-outer');
  if (!container) return;
  
  const leftArrow = container.querySelector('.slide-arrow2.left');
  const rightArrow = container.querySelector('.slide-arrow2.right');
  
  if (!leftArrow || !rightArrow) return;
  
  const isAtStart = carousel.scrollLeft <= 10;
  const isAtEnd = carousel.scrollLeft >= carousel.scrollWidth - carousel.clientWidth - 10;
  
  // Update left arrow
  leftArrow.style.opacity = isAtStart ? '0.3' : '0.87';
  leftArrow.style.cursor = isAtStart ? 'default' : 'pointer';
  leftArrow.style.pointerEvents = isAtStart ? 'none' : 'auto';
  
  // Update right arrow
  rightArrow.style.opacity = isAtEnd ? '0.3' : '0.87';
  rightArrow.style.cursor = isAtEnd ? 'default' : 'pointer';
  rightArrow.style.pointerEvents = isAtEnd ? 'none' : 'auto';
}

// Initialize all carousels on page load
window.addEventListener('DOMContentLoaded', function() {
  const carouselIds = [
    'video-carousel', 
    'live-carousel', 
    'ebook-carousel', 
    'test-carousel',
    'bundle-carousel'
  ];
  
  carouselIds.forEach(function(carouselId) {
    const carousel = document.getElementById(carouselId);
    if (!carousel) return; // Exit silently, no warning
    
    // Set smooth scroll behavior
    carousel.style.scrollBehavior = 'smooth';
    
    // Listen to scroll events
    carousel.addEventListener('scroll', function() {
      updateCarouselArrows(carouselId);
    });
    
    // Listen to resize events
    window.addEventListener('resize', function() {
      updateCarouselArrows(carouselId);
    });
    
    // Initial arrow state update
    updateCarouselArrows(carouselId);
  });
});
