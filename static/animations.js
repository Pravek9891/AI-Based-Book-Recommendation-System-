// Initialize Lenis Smooth Scroll
const lenis = new Lenis()

function raf(time) {
    lenis.raf(time)
    requestAnimationFrame(raf)
}
requestAnimationFrame(raf)

// GSAP ScrollTrigger Integration
lenis.on('scroll', ScrollTrigger.update)

gsap.ticker.add((time) => {
    lenis.raf(time * 1000)
})

gsap.ticker.lagSmoothing(0)

// Custom Magnetic Cursor
const cursor = document.querySelector('.cursor-follower');
let mouseX = 0, mouseY = 0;
let cursorX = 0, cursorY = 0;

window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
});

function animateCursor() {
    cursorX += (mouseX - cursorX) * 0.15;
    cursorY += (mouseY - cursorY) * 0.15;
    cursor.style.transform = `translate3d(${cursorX - 10}px, ${cursorY - 10}px, 0)`;
    requestAnimationFrame(animateCursor);
}
animateCursor();

// Hero Text Reveal
gsap.from(".hero h1", {
    y: 100,
    opacity: 0,
    duration: 1.5,
    ease: "power4.out",
    delay: 0.5
});

gsap.from(".hero p", {
    y: 50,
    opacity: 0,
    duration: 1.2,
    ease: "power3.out",
    delay: 0.8
});

// Staggered Book Cards Reveal
gsap.from(".book-card", {
    scrollTrigger: {
        trigger: ".book-container",
        start: "top 80%",
    },
    y: 80,
    opacity: 0,
    duration: 1,
    stagger: 0.1,
    ease: "expo.out"
});

// Magnetic Buttons Effect
const buttons = document.querySelectorAll('.btn-glass');
buttons.forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;

        gsap.to(btn, {
            x: x * 0.3,
            y: y * 0.3,
            duration: 0.4,
            ease: "power2.out"
        });

        gsap.to(cursor, {
            scale: 2,
            duration: 0.3
        });
    });

    btn.addEventListener('mouseleave', () => {
        gsap.to(btn, {
            x: 0,
            y: 0,
            duration: 0.6,
            ease: "elastic.out(1, 0.3)"
        });

        gsap.to(cursor, {
            scale: 1,
            duration: 0.3
        });
    });
});
