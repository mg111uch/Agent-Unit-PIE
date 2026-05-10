// Three.js Graph Visualization for ArguGod (Topic-Agnostic + LLM Mindmap)
class GraphVisualization {
    constructor() {
        this.currentTopic = "theism_atheism";
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.nodeObjects = [];
        this.edgeObjects = [];
        this.graphData = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.isAnimating = true;

        this.init();
        this.loadTopics();
        this.loadGraph();
        this.setupEventListeners();
        this.setupWebSocket();
    }

    init() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);

        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.camera.position.z = 30;

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById('canvas-container').appendChild(this.renderer.domElement);

        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        this.scene.add(directionalLight);

        this.setupMouseControls();
        window.addEventListener('resize', () => this.onWindowResize(), false);
    }

    setupMouseControls() {
        let isMouseDown = false;
        let mouseX = 0, mouseY = 0;
        let targetRotationX = 0, targetRotationY = 0;

        this.renderer.domElement.addEventListener('mousedown', (event) => {
            isMouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        this.renderer.domElement.addEventListener('mousemove', (event) => {
            if (isMouseDown) {
                const deltaX = event.clientX - mouseX;
                const deltaY = event.clientY - mouseY;
                targetRotationY += deltaX * 0.01;
                targetRotationX += deltaY * 0.01;
                mouseX = event.clientX;
                mouseY = event.clientY;
            }
        });

        this.renderer.domElement.addEventListener('mouseup', () => isMouseDown = false);
        this.renderer.domElement.addEventListener('click', (event) => this.onMouseClick(event));
        this.renderer.domElement.addEventListener('wheel', (event) => {
            this.camera.position.z += event.deltaY * 0.01;
            this.camera.position.z = Math.max(5, Math.min(100, this.camera.position.z));
        });
    }

    onMouseClick(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.nodeObjects);

        if (intersects.length > 0) {
            this.onNodeClick(intersects[0].object);
        }
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'graph_update') {
                this.graphData = message.data;
                this.createGraph();
            }
        };
    }

    async loadTopics() {
        const res = await fetch('/api/topics');
        const data = await res.json();
        const select = document.getElementById('topic-select');
        select.innerHTML = data.topics.map(t => 
            `<option value="${t}" ${t === this.currentTopic ? 'selected' : ''}>${t}</option>`
        ).join('');
    }

    async loadGraph() {
        const res = await fetch(`/api/graph?topic=${this.currentTopic}`);
        this.graphData = await res.json();
        this.createGraph();
    }

    createGraph() {
        if (!this.graphData) return;
        this.clearGraph();

        this.graphData.nodes.forEach((nodeData, index) => {
            const node = this.createNode(nodeData, index);
            this.nodeObjects.push(node);
            this.scene.add(node);
        });

        this.graphData.edges.forEach(edgeData => {
            const edge = this.createEdge(edgeData);
            if (edge) {
                this.edgeObjects.push(edge);
                this.scene.add(edge);
            }
        });

        this.animate();
    }

    createNode(nodeData, index) {
        const geometry = new THREE.SphereGeometry(1, 16, 16);
        let color = nodeData.side === 'pro' ? 0x00aa00 : 
                   (nodeData.side === 'con' ? 0xaa0000 : 0x888888);

        const material = new THREE.MeshPhongMaterial({ color: color, transparent: true, opacity: 0.8 });
        const sphere = new THREE.Mesh(geometry, material);

        const angle = (index / this.graphData.nodes.length) * Math.PI * 2;
        const radius = 12;
        sphere.position.x = Math.cos(angle) * radius;
        sphere.position.y = Math.sin(angle) * radius;
        sphere.position.z = (Math.random() - 0.5) * 8;

        sphere.userData = nodeData;
        return sphere;
    }

    createEdge(edgeData) {
        const source = this.nodeObjects.find(n => n.userData.name === edgeData.source);
        const target = this.nodeObjects.find(n => n.userData.name === edgeData.target);
        
        if (!source || !target) {
            console.warn("Edge skipped:", edgeData);
            return null;
        }

        const points = [source.position, target.position];
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 2 });
        return new THREE.Line(geometry, material);
    }

    onNodeClick(node) {
        this.nodeObjects.forEach(n => { n.material.opacity = 0.6; n.scale.set(1,1,1); });
        node.material.opacity = 1.0;
        node.scale.set(1.3, 1.3, 1.3);

        const data = node.userData;
        alert(`Node: ${data.name}\nSide: ${data.side}\nPremise: ${data.premise}`);
    }

    clearGraph() {
        this.nodeObjects.forEach(obj => this.scene.remove(obj));
        this.edgeObjects.forEach(obj => this.scene.remove(obj));
        this.nodeObjects = [];
        this.edgeObjects = [];
    }

    setupEventListeners() {
        document.getElementById('topic-select').addEventListener('change', e => {
            this.currentTopic = e.target.value;
            this.loadGraph();
        });

        document.getElementById('compile-btn').addEventListener('click', async () => {
            const status = document.getElementById('status');
            status.textContent = 'Compiling with Gemini...';
            await fetch(`/api/compile/${this.currentTopic}`, { method: 'POST' });
            status.textContent = '✅ Compiled & Mindmap updated';
            this.loadGraph();
        });

        document.getElementById('mindmap-btn').addEventListener('click', async () => {
            const res = await fetch('/api/mindmap');
            const mm = await res.json();
            let text = `🧠 Your Personal Mindmap (LLM-controlled)\n\n`;
            text += `Topics explored: ${mm.total_topics_explored || 0}\n\n`;
            Object.keys(mm.topics || {}).forEach(t => {
                text += `${t}: depth ${mm.topics[t].depth_score} | confidence ${mm.topics[t].confidence}\n`;
            });
            alert(text);
        });
    }

    animate() {
        if (!this.isAnimating) return;
        requestAnimationFrame(() => this.animate());

        const time = Date.now() * 0.001;
        this.nodeObjects.forEach((node, i) => {
            if (node.visible) node.position.z = Math.sin(time + i) * 0.5;
        });

        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new GraphVisualization();
});