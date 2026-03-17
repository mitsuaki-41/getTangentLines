import inkex
from inkex import PathElement
import math

class TangentGenerator(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--line_type", type=str, default="external")
        pars.add_argument("--use_custom_style", type=inkex.Boolean, default=False)
        pars.add_argument("--custom_width", type=float, default=1.0)
        pars.add_argument("--line_cap", type=str, default="butt")
        
    def effect(self):
        if len(self.svg.selection) != 2:
            inkex.errormsg("Select a pair of circles.")
            return
            
        nodes = list(self.svg.selection.values())

        # --- スタイルの決定 ---
        target_style = nodes[0].style.copy()
        target_style['fill'] = 'none'
        if self.options.use_custom_style:
            target_style['stroke'] = '#000000'
            target_style['stroke-width'] = self.svg.viewport_to_unit(f"{self.options.custom_width}px")
            target_style['stroke-linecap'] = self.options.line_cap
        else:
            stroke = target_style.get('stroke')
            if stroke == 'none':
                target_style['stroke'] = '#000000'
                target_style['stroke-width'] = str(self.svg.viewport_to_unit("1px"))

        circles = []
        for node in nodes:
            try:
                bbox = node.bounding_box()
                w = bbox.width
                h = bbox.height
                
                # 比率チェック
                if abs(w - h) > (max(w, h) * 0.001):
                    inkex.errormsg("[Object] Only 1 : 1 width to height ratio is supported.")
                    return

                circles.append({
                    'c': (bbox.center.x, bbox.center.y),
                    'r': w / 2.0
                })
            except Exception:
                continue

        is_internal = (self.options.line_type == "internal")
        self.calculate_and_draw(circles[0], circles[1], target_style, is_internal)

    def calculate_and_draw(self, c1, c2, style, is_internal):
        x1, y1 = c1['c']
        x2, y2 = c2['c']
        r1, r2 = c1['r'], c2['r']
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx**2 + dy**2)

        try:
            target_r = (r1 + r2) if is_internal else (r1 - r2)
            ratio = target_r / dist
            
            if abs(ratio) > 1.0:
                msg = "The circles are too close together to draw an intangent." if is_internal else "One circle is contained within the other."
                inkex.errormsg(msg)
                return

            angle_centers = math.atan2(dy, dx)
            angle_offset = math.acos(ratio)

            for sign in [1, -1]:
                alpha = angle_centers + (sign * angle_offset)
                beta = (alpha + math.pi) if is_internal else alpha
                
                p1x, p1y = x1 + r1 * math.cos(alpha), y1 + r1 * math.sin(alpha)
                p2x, p2y = x2 + r2 * math.cos(beta), y2 + r2 * math.sin(beta)

                self.draw_line(p1x, p1y, p2x, p2y, style)
        except Exception as e:
            inkex.errormsg(f"Calculation Error: {e}")

    def draw_line(self, x1, y1, x2, y2, style):
        line_path = f"M {x1},{y1} L {x2},{y2}"
        element = PathElement()
        element.set('d', line_path)
        element.style = style
        self.svg.get_current_layer().add(element)

if __name__ == '__main__':
    TangentGenerator().run()
