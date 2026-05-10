import time
import math

class ScrollAnimator:
    """
    A standalone class to handle hyperscroll-style animations (Lerp + Snapping).
    Extracted from Project Conveyor.
    """

    def __init__(self, lerp_factor=0.15, snap_delay=0.20):
        self.current_offset = 0.0
        self.target_offset = 0.0
        
        # Configuration
        self.lerp_factor = lerp_factor
        self.snap_delay = snap_delay
        
        # State
        self.last_input_time = time.time()
        self.is_moving = False
        self.is_snapping = False

    def update(self, window_widths, screen_width, gap=5, modifier_pressed=False):
        """
        Updates the animation state and calculates the next offset.
        Call this in a loop.
        
        :param window_widths: List of widths for all managed windows.
        :param screen_width: Total width of the screen.
        :param gap: Gap between windows.
        :param modifier_pressed: True if the user is currently interacting (scrolling).
        :return: (current_offset, needs_redraw)
        """
        now = time.time()
        diff = self.target_offset - self.current_offset
        needs_redraw = False

        # 1. Handle Smooth Movement (Lerp)
        if abs(diff) > 0.1:
            self.is_moving = True
            current_lerp = self.lerp_factor
            
            # Adaptive slowing down as we get closer
            if abs(diff) < 50: 
                current_lerp *= 0.8
                
            self.current_offset += diff * current_lerp
            needs_redraw = True
        else:
            # Snap to final position once close enough
            if self.is_moving:
                self.current_offset = self.target_offset
                needs_redraw = True
                self.is_moving = False
                self.is_snapping = False
            
            # 2. Handle Snapping (Auto-centering windows)
            if not modifier_pressed and not self.is_snapping:
                if now - self.last_input_time > self.snap_delay:
                    snap_target = self.calculate_snap_target(window_widths, screen_width, gap)
                    if abs(self.target_offset - snap_target) > 1.0:
                        self.target_offset = snap_target
                        self.is_snapping = True

        return self.current_offset, needs_redraw

    def calculate_snap_target(self, window_widths, screen_width, gap):
        """Calculates the offset required to center the nearest window."""
        if not window_widths:
            return 0
            
        acc_x = 0
        screen_center = screen_width / 2
        min_dist = float('inf')
        best_offset = self.target_offset
        
        for w in window_widths:
            # World-space center of this window
            win_center_world = acc_x + (w / 2)
            
            # Distance from current viewport center to window center
            dist = abs(self.target_offset - win_center_world + screen_center)
            
            if dist < min_dist:
                min_dist = dist
                best_offset = win_center_world - screen_center
                
            acc_x += w + gap
            
        return best_offset

    def get_central_index(self, window_widths, screen_width, gap):
        """Finds the index of the window currently closest to the screen center."""
        if not window_widths:
            return -1
            
        screen_center = screen_width / 2
        min_dist = float('inf')
        central_idx = -1
        curr_x = -self.current_offset
        
        for i, w in enumerate(window_widths):
            win_center = curr_x + (w / 2)
            dist = abs(win_center - screen_center)
            if dist < min_dist:
                min_dist = dist
                central_idx = i
            curr_x += w + gap
            
        return central_idx

    def handle_input(self, delta_x):
        """Update target offset based on input (e.g. mouse scroll or keyboard)."""
        self.target_offset += delta_x
        self.last_input_time = time.time()
        self.is_snapping = False # Interrupt snapping on manual input

# Example Usage:
"""
animator = ScrollAnimator()
while True:
    offset, redraw = animator.update(
        window_widths=[800, 600, 1000],
        screen_width=1920,
        modifier_pressed=keyboard.is_pressed('alt')
    )
    if redraw:
        apply_layout(offset)
    time.sleep(0.008)
"""
