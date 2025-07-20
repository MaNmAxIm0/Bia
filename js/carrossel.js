export function initCarousel(carouselElement) {
  const slidesContainer = carouselElement.querySelector('.carousel-slides');
  const slides = Array.from(slidesContainer.children);
  const prevBtn = carouselElement.querySelector('.carousel-btn.prev');
  const nextBtn = carouselElement.querySelector('.carousel-btn.next');
  const dotsContainer = carouselElement.querySelector('.carousel-dots');
  if (!slides.length) {
    console.warn("Carousel slides not found.");
    return;
  }
  let currentIndex = 0;
  let autoPlayInterval;
  slides.forEach((_, index) => {
    const dot = document.createElement('span');
    dot.classList.add('dot');
    if (index === 0) dot.classList.add('active');
    dot.addEventListener('click', () => goToSlide(index));
    dotsContainer.appendChild(dot);
  });
  const dots = Array.from(dotsContainer.children);
  function updateCarousel() {
    slidesContainer.style.transform = `translateX(-${currentIndex * 100}%)`;
    dots.forEach((dot, index) => {
      dot.classList.toggle('active', index === currentIndex);
    });
  }
  function goToSlide(index) {
    currentIndex = (index + slides.length) % slides.length;
    updateCarousel();
    resetAutoPlay();
  }
  function nextSlide() {
    goToSlide(currentIndex + 1);
  }
  function prevSlide() {
    goToSlide(currentIndex - 1);
  }
  function startAutoPlay() {
    autoPlayInterval = setInterval(nextSlide, 5000);
  }
  function stopAutoPlay() {
    clearInterval(autoPlayInterval);
  }
  function resetAutoPlay() {
    stopAutoPlay();
    startAutoPlay();
  }
  if (prevBtn) {
    prevBtn.addEventListener('click', prevSlide);
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', nextSlide);
  }
  updateCarousel();
  startAutoPlay();
  carouselElement.addEventListener('mouseenter', stopAutoPlay);
  carouselElement.addEventListener('mouseleave', startAutoPlay);
}