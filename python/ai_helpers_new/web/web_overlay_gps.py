
# web_overlay_gps.py - 실제 구현 코드

class WebOverlayGPS:
    """웹 브라우저 오버레이 GPS 시스템"""

    def __init__(self, session_id):
        self.session_id = session_id
        self.markers = []
        self.active_element = None
        self.is_active = False

    def inject_overlay(self, page):
        """페이지에 오버레이 주입"""
        # Canvas 생성 JavaScript
        overlay_js = """
        if (!window.webGPS) {
            const canvas = document.createElement('canvas');
            canvas.id = 'web-gps-overlay';
            canvas.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                pointer-events: none;
                z-index: 999999;
            `;
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            document.body.appendChild(canvas);

            window.webGPS = {
                canvas: canvas,
                ctx: canvas.getContext('2d'),
                markers: [],

                showClickMarker: function(x, y, label) {
                    this.ctx.clearRect(0, 0, canvas.width, canvas.height);
                    this.ctx.strokeStyle = '#FF0000';
                    this.ctx.lineWidth = 3;
                    this.ctx.beginPath();
                    this.ctx.arc(x, y, 20, 0, 2 * Math.PI);
                    this.ctx.stroke();

                    if (label) {
                        this.ctx.fillStyle = '#FF0000';
                        this.ctx.font = 'bold 14px Arial';
                        this.ctx.fillText(label, x + 25, y - 25);
                    }
                },

                highlightElement: function(selector) {
                    const element = document.querySelector(selector);
                    if (element) {
                        const rect = element.getBoundingClientRect();
                        this.ctx.strokeStyle = '#0066FF';
                        this.ctx.lineWidth = 3;
                        this.ctx.setLineDash([5, 5]);
                        this.ctx.strokeRect(rect.left, rect.top, rect.width, rect.height);
                        this.ctx.setLineDash([]);
                    }
                },

                drawPath: function(points) {
                    this.ctx.strokeStyle = '#00FF00';
                    this.ctx.lineWidth = 2;
                    this.ctx.setLineDash([10, 5]);
                    this.ctx.beginPath();
                    points.forEach((point, i) => {
                        if (i === 0) this.ctx.moveTo(point.x, point.y);
                        else this.ctx.lineTo(point.x, point.y);
                    });
                    this.ctx.stroke();
                    this.ctx.setLineDash([]);
                }
            };
        }
        """
        page.evaluate(overlay_js)
        return True

    def mark_click_location(self, x, y, label="Click Here"):
        """클릭 위치 마킹"""
        js_code = f"window.webGPS.showClickMarker({x}, {y}, '{label}');"
        return js_code

    def highlight_element(self, selector):
        """요소 하이라이트"""
        js_code = f"window.webGPS.highlightElement('{selector}');"
        return js_code

    def show_path(self, waypoints):
        """경로 표시"""
        points_str = json.dumps(waypoints)
        js_code = f"window.webGPS.drawPath({points_str});"
        return js_code
