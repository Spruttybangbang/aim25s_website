// WebGL Animated Gradient Background
(function() {
    const canvas = document.getElementById('gradient-canvas');

    if (!canvas) {
        console.warn('Gradient canvas not found');
        return;
    }

    const gl = canvas.getContext('webgl', {
        alpha: false,
        antialias: true,
        preserveDrawingBuffer: false
    }) || canvas.getContext('experimental-webgl', {
        alpha: false,
        antialias: true,
        preserveDrawingBuffer: false
    });

    if (!gl) {
        console.warn('WebGL not supported, using CSS fallback');
        // CSS fallback - Lavender dreams gradient
        document.body.style.background = 'linear-gradient(135deg, #f7f4ea, #ebe7e6, #ded9e2, #c0b9dd)';
        document.body.style.backgroundSize = '400% 400%';
        document.body.style.animation = 'gradient 20s ease infinite';
        const style = document.createElement('style');
        style.textContent = '@keyframes gradient { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }';
        document.head.appendChild(style);
        return;
    }

    console.log('WebGL gradient initialized');

    // Vertex shader
    const vertexShaderSource = `
        attribute vec2 position;
        void main() {
            gl_Position = vec4(position, 0.0, 1.0);
        }
    `;

    // Fragment shader with soft lavender palette
    const fragmentShaderSource = `
        precision mediump float;
        uniform vec2 resolution;
        uniform float time;

        // Hash function for pseudo-random
        float hash(vec2 p) {
            return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
        }

        // Simple noise
        float noise(vec2 p) {
            vec2 i = floor(p);
            vec2 f = fract(p);
            f = f * f * (3.0 - 2.0 * f);

            float a = hash(i);
            float b = hash(i + vec2(1.0, 0.0));
            float c = hash(i + vec2(0.0, 1.0));
            float d = hash(i + vec2(1.0, 1.0));

            return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
        }

        // Fractal Brownian Motion for cloud-like softness
        float fbm(vec2 p) {
            float value = 0.0;
            float amplitude = 0.5;
            float frequency = 1.0;

            for(int i = 0; i < 4; i++) {
                value += amplitude * noise(p * frequency);
                frequency *= 2.0;
                amplitude *= 0.5;
            }

            return value;
        }

        // Soft lavender and grey palette
        vec3 getColor(float t) {
            t = mod(t, 1.0);

            // Floral White #f7f4ea
            vec3 c1 = vec3(0.969, 0.957, 0.918);
            // Alabaster Grey #ebe7e6
            vec3 c2 = vec3(0.922, 0.906, 0.902);
            // Lavender #ded9e2
            vec3 c3 = vec3(0.871, 0.851, 0.886);
            // Periwinkle #c0b9dd
            vec3 c4 = vec3(0.753, 0.725, 0.867);

            if (t < 0.25) {
                return mix(c1, c2, t * 4.0);
            } else if (t < 0.5) {
                return mix(c2, c3, (t - 0.25) * 4.0);
            } else if (t < 0.75) {
                return mix(c3, c4, (t - 0.5) * 4.0);
            } else {
                return mix(c4, c1, (t - 0.75) * 4.0);
            }
        }

        void main() {
            vec2 uv = gl_FragCoord.xy / resolution;

            // Create very soft, cloud-like flowing pattern
            float n1 = fbm(uv * 1.6 + time * 0.03);
            float n2 = fbm(uv * 2.0 - vec2(time * 0.04, time * 0.025));
            float n3 = fbm(uv * 1.3 + vec2(sin(time * 0.025) * 1.8, cos(time * 0.03) * 1.8));

            // Combine for extremely soft, ethereal movement
            float combined = (n1 + n2 + n3) / 3.0;

            // Add very gentle wave motion like soft fabric
            float wave = sin(combined * 2.5 + time * 0.15) * 0.06;
            combined += wave;

            // Map to color
            vec3 color = getColor(combined + time * 0.01);

            // Add very subtle brightness variation
            float brightness = 0.98 + sin(time * 0.12 + uv.x * 2.0 + uv.y * 1.5) * 0.02;
            color *= brightness;

            // Slight cool tint for dreamy quality
            color.b *= 1.01;

            gl_FragColor = vec4(color, 1.0);
        }
    `;

    function compileShader(source, type) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('Shader compile error:', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }

        return shader;
    }

    const vertexShader = compileShader(vertexShaderSource, gl.VERTEX_SHADER);
    const fragmentShader = compileShader(fragmentShaderSource, gl.FRAGMENT_SHADER);

    if (!vertexShader || !fragmentShader) {
        console.error('Shader compilation failed');
        return;
    }

    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error('Program link error:', gl.getProgramInfoLog(program));
        return;
    }

    gl.useProgram(program);

    // Setup geometry
    const positions = new Float32Array([
        -1, -1,
         1, -1,
        -1,  1,
         1,  1
    ]);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

    const positionLocation = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(positionLocation);
    gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

    // Get uniform locations
    const resolutionLocation = gl.getUniformLocation(program, 'resolution');
    const timeLocation = gl.getUniformLocation(program, 'time');

    // Resize canvas
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.uniform2f(resolutionLocation, canvas.width, canvas.height);
    }

    window.addEventListener('resize', resize);
    resize();

    // Animation loop
    let startTime = Date.now();

    function render() {
        const time = (Date.now() - startTime) * 0.001;
        gl.uniform1f(timeLocation, time);

        gl.clearColor(0.97, 0.96, 0.92, 1.0);
        gl.clear(gl.COLOR_BUFFER_BIT);

        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        requestAnimationFrame(render);
    }

    render();
})();
