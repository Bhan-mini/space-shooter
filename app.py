import streamlit as st
import streamlit.components.v1 as components

# Cấu hình ẩn thanh tiêu đề mặc định của Streamlit để giao diện rộng tuyệt đối
st.set_page_config(page_title="Space Shooter Game", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

# Ẩn header và footer mặc định của Streamlit trên web để game tràn viền
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Tạo trạng thái lưu việc người dùng đã bấm nút bật âm thanh chưa
if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = False

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if not st.session_state.sound_enabled:
        if st.button("🔊 Bấm để Bật Âm Thanh & Chơi Game", use_container_width=True):
            st.session_state.sound_enabled = True
            st.rerun()

# Truyền trạng thái âm thanh vào JavaScript thông qua biến soundActive
sound_flag = "true" if st.session_state.sound_enabled else "false"

game_code = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Space Shooter Fullscreen</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100vh;
            background: #090915;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: white;
            touch-action: none;
        }}
        canvas {{
            background: radial-gradient(circle at center, #1a1a3a 0%, #050512 100%);
            box-shadow: 0 0 30px rgba(0, 230, 255, 0.4);
            border-radius: 8px;
            width: 100vw;
            height: 100vh;
            max-width: 500px;
            max-height: 100vh;
            object-fit: contain;
            display: block;
        }}
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="400" height="650"></canvas>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");

        const isSoundActive = {sound_flag};
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        let audioCtx = null;

        function initAudio() {{
            if (!isSoundActive) return;
            if (!audioCtx) {{ audioCtx = new AudioCtx(); }}
            if (audioCtx.state === 'suspended') {{ audioCtx.resume(); }}
        }}

        // Âm lượng vừa phải, không bị lấn át hay chói tai
        function playSound(type) {{
            if (!isSoundActive || !audioCtx) return;
            try {{
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                const now = audioCtx.currentTime;

                if (type === 'laser') {{
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(800, now);
                    osc.frequency.exponentialRampToValueAtTime(100, now + 0.1);
                    gain.gain.setValueAtTime(0.08, now);
                    gain.gain.exponentialRampToValueAtTime(0.005, now + 0.1);
                    osc.start(now); osc.stop(now + 0.1);
                }} else if (type === 'explosion') {{
                    osc.type = 'square';
                    osc.frequency.setValueAtTime(150, now);
                    osc.frequency.exponentialRampToValueAtTime(30, now + 0.2);
                    gain.gain.setValueAtTime(0.12, now);
                    gain.gain.exponentialRampToValueAtTime(0.005, now + 0.2);
                    osc.start(now); osc.stop(now + 0.2);
                }} else if (type === 'hit') {{
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(120, now);
                    osc.frequency.linearRampToValueAtTime(40, now + 0.3);
                    gain.gain.setValueAtTime(0.15, now);
                    gain.gain.exponentialRampToValueAtTime(0.005, now + 0.3);
                    osc.start(now); osc.stop(now + 0.3);
                }} else if (type === 'levelup') {{
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(300, now);
                    osc.frequency.setValueAtTime(500, now + 0.1);
                    osc.frequency.setValueAtTime(800, now + 0.2);
                    gain.gain.setValueAtTime(0.1, now);
                    gain.gain.exponentialRampToValueAtTime(0.005, now + 0.4);
                    osc.start(now); osc.stop(now + 0.4);
                }}
            }} catch (e) {{ console.log(e); }}
        }}

        // Tự động phát âm thanh mở màn ngay khi game tải xong và âm thanh đã được bật từ nút Streamlit
        if (isSoundActive) {{
            window.addEventListener('load', () => {{
                initAudio();
                setTimeout(() => {{
                    playSound('levelup');
                }}, 200);
            }});
        }}

        let score = 0, lives = 3, level = 1, isGameOver = false, levelUpTimer = 0;
        let player = {{ x: canvas.width / 2 - 20, y: canvas.height - 70, width: 40, height: 40, speed: 7 }};
        let bullets = [], enemyBullets = [], enemies = [], particles = [];

        function initEnemies() {{
            enemies = [];
            let rows = Math.min(3 + Math.floor(level / 2), 6);
            let cols = 7;
            for (let r = 0; r < rows; r++) {{
                for (let c = 0; c < cols; c++) {{
                    enemies.push({{
                        x: 35 + c * 48, y: 60 + r * 38,
                        width: 34, height: 26, alive: true,
                        shootChance: 0.0005 + (level * 0.0003)
                    }});
                }}
            }}
        }}
        initEnemies();

        let keys = {{}};
        window.addEventListener("keydown", (e) => {{ initAudio(); keys[e.key] = true; }});
        window.addEventListener("keyup", (e) => {{ keys[e.key] = false; }});

        canvas.addEventListener("mousemove", (e) => {{
            initAudio();
            let rect = canvas.getBoundingClientRect();
            let scaleX = canvas.width / rect.width;
            player.x = (e.clientX - rect.left) * scaleX - player.width / 2;
        });

        canvas.addEventListener("touchmove", (e) => {{
            initAudio();
            if (e.touches.length > 0) {{
                let rect = canvas.getBoundingClientRect();
                let scaleX = canvas.width / rect.width;
                player.x = (e.touches[0].clientX - rect.left) * scaleX - player.width / 2;
            }}
            e.preventDefault();
        }}, {{ passive: false }});

        function handleRestart() {{
            initAudio();
            if (isGameOver) {{
                score = 0; lives = 3; level = 1; isGameOver = false;
                bullets = []; enemyBullets = []; initEnemies();
            }}
        }}
        canvas.addEventListener("click", handleRestart);
        canvas.addEventListener("touchend", handleRestart);

        setInterval(() => {{
            if (!isGameOver && levelUpTimer <= 0) {{
                bullets.push({{ x: player.x + player.width / 2 - 3, y: player.y, width: 6, height: 14, speed: 8 }});
                playSound('laser');
            }}
        }}, 220);

        function update() {{
            if (isGameOver) return;
            if (levelUpTimer > 0) {{
                levelUpTimer--;
                if (levelUpTimer === 0) {{ initEnemies(); }}
                return;
            }}

            if (keys["ArrowLeft"] || keys["a"] || keys["A"]) player.x -= player.speed;
            if (keys["ArrowRight"] || keys["d"] || keys["D"]) player.x += player.speed;

            if (player.x < 0) player.x = 0;
            if (player.x > canvas.width - player.width) player.x = canvas.width - player.width;

            bullets.forEach((b, index) => {{
                b.y -= b.speed;
                if (b.y < 0) bullets.splice(index, 1);
            }});

            enemyBullets.forEach((eb, index) => {{
                eb.y += eb.speed;
                if (eb.x < player.x + player.width && eb.x + eb.width > player.x && eb.y < player.y + player.height && eb.y + eb.height > player.y) {{
                    enemyBullets.splice(index, 1);
                    lives--;
                    playSound('hit');
                    createExplosion(player.x + player.width/2, player.y + player.height/2, "#00ffff");
                    if (lives <= 0) isGameOver = true;
                }} else if (eb.y > canvas.height) {{
                    enemyBullets.splice(index, 1);
                }}
            }});

            let allDead = true;
            enemies.forEach((e) => {{
                if (!e.alive) return;
                allDead = false;

                if (Math.random() < e.shootChance) {{
                    enemyBullets.push({{ x: e.x + e.width / 2 - 2, y: e.y + e.height, width: 5, height: 10, speed: 3 + level * 0.5 }});
                }}

                bullets.forEach((b, bIndex) => {{
                    if (b.x < e.x + e.width && b.x + b.width > e.x && b.y < e.y + e.height && b.y + e.height > e.y) {{
                        e.alive = false;
                        bullets.splice(bIndex, 1);
                        score += 100 * level;
                        playSound('explosion');
                        createExplosion(e.x + e.width/2, e.y + e.height/2, "#ff5555");
                    }}
                }});
            }});

            if (allDead) {{
                level++;
                levelUpTimer = 90;
                playSound('levelup');
            }}

            particles.forEach((p, index) => {{
                p.x += p.dx; p.y += p.dy; p.life--;
                if (p.life <= 0) particles.splice(index, 1);
            }});
        }}

        function createExplosion(x, y, color) {{
            for (let i = 0; i < 10; i++) {{
                particles.push({{
                    x: x, y: y,
                    dx: (Math.random() - 0.5) * 6,
                    dy: (Math.random() - 0.5) * 6,
                    radius: Math.random() * 3 + 1,
                    color: color, life: 25
                }});
            }}
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = "#ffffff";
            ctx.fillRect(30, (Date.now() / 20) % canvas.height, 2, 2);
            ctx.fillRect(200, (Date.now() / 15 + 100) % canvas.height, 1.5, 1.5);
            ctx.fillRect(340, (Date.now() / 25 + 200) % canvas.height, 2, 2);

            ctx.fillStyle = "#00f0ff";
            ctx.beginPath();
            ctx.moveTo(player.x + player.width / 2, player.y);
            ctx.lineTo(player.x + player.width, player.y + player.height);
            ctx.lineTo(player.x + player.width / 2, player.y + player.height - 8);
            ctx.lineTo(player.x, player.y + player.height);
            ctx.closePath();
            ctx.fill();

            ctx.fillStyle = "#33ff33";
            bullets.forEach(b => ctx.fillRect(b.x, b.y, b.width, b.height));

            ctx.fillStyle = "#ff3333";
            enemyBullets.forEach(eb => ctx.fillRect(eb.x, eb.y, eb.width, eb.height));

            enemies.forEach(e => {{
                if (e.alive) {{
                    ctx.fillStyle = "#ff0055";
                    ctx.fillRect(e.x, e.y, e.width, e.height);
                    ctx.fillStyle = "#ffff00";
                    ctx.fillRect(e.x + 5, e.y + 4, e.width - 10, 6);
                }}
            }});

            particles.forEach(p => {{
                ctx.fillStyle = p.color;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fill();
            }});

            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 15px Arial";
            ctx.fillText("SCORE: " + score, 15, 30);
            ctx.fillText("LVL: " + level, canvas.width / 2 - 20, 30);
            ctx.fillText("LIVES: " + "❤️".repeat(lives), canvas.width - 105, 30);

            if (levelUpTimer > 0) {{
                ctx.fillStyle = "#00ffff";
                ctx.font = "bold 28px Arial";
                ctx.textAlign = "center";
                ctx.fillText("LEVEL " + level, canvas.width / 2, canvas.height / 2);
                ctx.textAlign = "left";
            }}

            if (isGameOver) {{
                ctx.fillStyle = "rgba(0,0,0,0.8)";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = "#ff3333";
                ctx.font = "bold 30px Arial";
                ctx.textAlign = "center";
                ctx.fillText("GAME OVER", canvas.width / 2, canvas.height / 2 - 20);
                ctx.fillStyle = "#ffffff";
                ctx.font = "16px Arial";
                ctx.fillText("Điểm: " + score, canvas.width / 2, canvas.height / 2 + 15);
                ctx.fillStyle = "#00ffff";
                ctx.font = "14px Arial";
                ctx.fillText("Chạm/Nhấp để chơi lại", canvas.width / 2, canvas.height / 2 + 55);
                ctx.textAlign = "left";
            }}
        }}

        function gameLoop() {{
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }}

        gameLoop();
    </script>
</body>
</html>
"""

components.html(game_code, height=750, scrolling=False)
