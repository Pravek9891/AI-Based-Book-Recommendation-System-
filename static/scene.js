import * as THREE from 'https://cdn.skypack.dev/three@0.132.2';

let scene, camera, renderer, objects = [];

function init() {
    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;

    renderer = new THREE.WebGLRenderer({
        canvas: document.querySelector('#canvas-bg'),
        alpha: true,
        antialias: true
    });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);

    // Dynamic Lighting
    const pointLight = new THREE.PointLight(0x3b82f6, 2);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    const ambLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambLight);

    // Animated Floating Geometries
    const geometry = new THREE.IcosahedronGeometry(1.5, 0);
    const material = new THREE.MeshPhongMaterial({
        color: 0x3b82f6,
        wireframe: true,
        transparent: true,
        opacity: 0.08
    });

    for (let i = 0; i < 30; i++) {
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(
            (Math.random() - 0.5) * 20,
            (Math.random() - 0.5) * 20,
            (Math.random() - 0.5) * 10
        );
        mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
        const scale = Math.random() * 0.5 + 0.1;
        mesh.scale.set(scale, scale, scale);

        objects.push({
            mesh: mesh,
            speedX: (Math.random() - 0.5) * 0.005,
            speedY: (Math.random() - 0.5) * 0.005
        });
        scene.add(mesh);
    }

    animate();
}

function animate() {
    requestAnimationFrame(animate);

    objects.forEach(obj => {
        obj.mesh.rotation.x += 0.002;
        obj.mesh.rotation.y += 0.002;
        obj.mesh.position.x += obj.speedX + (mouseX * 0.00005);
        obj.mesh.position.y += obj.speedY - (mouseY * 0.00005);

        // Bounds check
        if (Math.abs(obj.mesh.position.x) > 12) obj.speedX *= -1;
        if (Math.abs(obj.mesh.position.y) > 10) obj.speedY *= -1;
    });

    renderer.render(scene, camera);
}

let mouseX = 0;
let mouseY = 0;

window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX - window.innerWidth / 2;
    mouseY = e.clientY - window.innerHeight / 2;
});

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

init();
