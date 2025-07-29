import sys
import os
import time
import RPi.GPIO as GPIO
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QUrl, QPoint, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from usb import setup

# Collect assets
setup()

# Current user
user = os.getlogin()

# GPIO configuration
SENSOR_PINS = {
    1: 32,
    2: 36,
    3: 38,
    4: 40
}
SHUTDOWN_PIN = 26  # GPIO pin for shutdown button
HOLD_DURATION = 4  # Seconds to hold for shutdown
GPIO.setmode(GPIO.BOARD)

class AnimatedWidget(QLabel):
    """Animated image widget."""
    def __init__(self, parent):
        super().__init__(parent)
        self.original_pixmap = None
        self.setAlignment(Qt.AlignCenter)
        self.hide()

        self.up_anim = QPropertyAnimation(self, b"pos")
        self.up_anim.setDuration(600)
        self.up_anim.setEasingCurve(QEasingCurve.OutBack)

        self.bounce_anim = QPropertyAnimation(self, b"pos")
        self.bounce_anim.setDuration(300)
        self.bounce_anim.setEasingCurve(QEasingCurve.InOutSine)

        self.down_anim = QPropertyAnimation(self, b"pos")
        self.down_anim.setDuration(700)
        self.down_anim.setEasingCurve(QEasingCurve.InOutSine)

        self.up_anim.finished.connect(self.start_bounce_anim)

    def start_bounce_anim(self):
        current_pos = self.pos()
        final_pos = QPoint(current_pos.x(), current_pos.y())
        self.bounce_anim.setStartValue(current_pos)
        self.bounce_anim.setEndValue(final_pos)
        self.bounce_anim.start()

    def set_image(self, pixmap):
        if not pixmap.isNull():
            self.original_pixmap = pixmap
            self.update_scaled_pixmap()
        else:
            self.clear()

    def update_scaled_pixmap(self):
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled_pixmap = self.original_pixmap.scaled(
                self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
        else:
            self.clear()

    def animate_in(self, target_pos):
        self.show()
        self.raise_()
        start_pos = QPoint(target_pos.x(), self.parent().height())
        overshoot_pos = QPoint(target_pos.x(), target_pos.y())
        self.up_anim.setStartValue(start_pos)
        self.up_anim.setEndValue(overshoot_pos)
        self.up_anim.start()

    def animate_out(self):
        current_pos = self.pos()
        end_pos = QPoint(current_pos.x(), self.parent().height())
        self.down_anim.setStartValue(current_pos)
        self.down_anim.setEndValue(end_pos)
        self.down_anim.start()

    def resizeEvent(self, event):
        self.update_scaled_pixmap()
        super().resizeEvent(event)

class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.margin = 20
        GPIO.setmode(GPIO.BOARD)
        self.check_media_files()
        self.setup_gpio()
        self.setup_ui()
        self.setup_media()
        self.current_active_key = None
        self.images = self.load_images()
        self.previous_states = {pin: GPIO.input(pin) for pin in SENSOR_PINS.values()}
        self.setup_sensor_check()
        self.setStyleSheet('background-color: black;')
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.showFullScreen()
        self.hide_cursor()

        self.shutdown_timer = QTimer(self)
        self.shutdown_timer.timeout.connect(self.check_shutdown_hold)
        self.shutdown_press_time = 0
        self.shutdown_alert_shown = False

    def hide_cursor(self):
        pixmap = QPixmap("/home/mohamad/Project/1.png")
        pixmap.fill(Qt.transparent)
        self.setCursor(QCursor(pixmap))

    def check_media_files(self):
        if not os.path.exists(f'/home/{user}/Project/main_video.mp4'):
            raise FileNotFoundError("Main video file not found")

    def load_images(self):
        return {
            1: self.load_image(f'/home/{user}/Project/1'),
            2: self.load_image(f'/home/{user}/Project/2'),
            3: self.load_image(f'/home/{user}/Project/3'),
            4: self.load_image(f'/home/{user}/Project/4')
        }

    def load_image(self, base_name):
        for ext in ['.png', '.jpg', '.jpeg', '.gif']:
            path = f"{base_name}{ext}"
            if os.path.exists(path):
                return QPixmap(path)
        print(f"Image not found for {base_name}")
        return QPixmap()

    def setup_gpio(self):
        for pin in SENSOR_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(SHUTDOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def setup_ui(self):
        self.setWindowTitle('Ad')
        self.setWindowFlags(Qt.FramelessWindowHint)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.IgnoreAspectRatio)
        self.video_widget.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_widget)

        self.widgets = {}
        for key in SENSOR_PINS.keys():
            widget = AnimatedWidget(self)
            self.widgets[key] = widget

    def calculate_widget_properties(self):
        num_widgets = len(SENSOR_PINS)
        total_margin = 2 * self.margin
        spacing_between = self.margin * (num_widgets - 1)
        available_width = self.width() - total_margin - spacing_between
        widget_width = available_width // num_widgets
        widget_height = int(self.height() // 2 * 0.9)

        positions = {}
        x = self.margin
        for key in sorted(SENSOR_PINS.keys()):
            positions[key] = (widget_width, widget_height, x, self.height())
            x += widget_width + self.margin

        last_key = max(SENSOR_PINS.keys())
        positions[last_key] = (widget_width, widget_height, self.width() - self.margin - widget_width, self.height())

        return positions

    def setup_media(self):
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.playlist = QMediaPlaylist()
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(f'/home/{user}/Project/main_video.mp4')))
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.media_player.setPlaylist(self.playlist)
        self.media_player.play()

    def setup_sensor_check(self):
        self.sensor_check_timer = QTimer(self)
        self.sensor_check_timer.timeout.connect(self.check_all_inputs)
        self.sensor_check_timer.start(100)

    def check_all_inputs(self):
        self.check_shutdown_button()
        self.check_sensors()

    def check_shutdown_button(self):
        current_state = GPIO.input(SHUTDOWN_PIN)

        if current_state == GPIO.HIGH:
            if self.shutdown_press_time == 0:
                self.shutdown_press_time = time.time()
                self.shutdown_timer.start(200)
        else:
            if self.shutdown_press_time > 0:
                self.reset_shutdown_timer()

    def check_shutdown_hold(self):
        if GPIO.input(SHUTDOWN_PIN) == GPIO.HIGH:
            elapsed = time.time() - self.shutdown_press_time
            if elapsed >= HOLD_DURATION:
                self.initiate_shutdown()
            else:
                if not self.shutdown_alert_shown:
                    self.show_shutdown_warning(elapsed)
        else:
            self.reset_shutdown_timer()

    def show_shutdown_warning(self, elapsed):
        remaining = HOLD_DURATION - int(elapsed)
        if remaining <= 3 and remaining > 0:
            self.shutdown_alert_shown = True
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(f"Hold shutdown button for {remaining} seconds to power off")
            msg.setWindowTitle("Shutdown Warning")
            msg.setStandardButtons(QMessageBox.NoButton)
            msg.show()

            time.sleep(3)
            os.system("sudo shutdown -h now")

    def reset_shutdown_timer(self):
        self.shutdown_timer.stop()
        self.shutdown_press_time = 0
        self.shutdown_alert_shown = False

    def initiate_shutdown(self):
        self.reset_shutdown_timer()
        GPIO.cleanup()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("System shutting down...")
        msg.setWindowTitle("Shutting Down")
        msg.setStandardButtons(QMessageBox.NoButton)
        msg.show()

    def check_sensors(self):
        for key, pin in SENSOR_PINS.items():
            current_state = GPIO.input(pin)
            prev_state = self.previous_states[pin]

            if current_state != prev_state:
                self.previous_states[pin] = current_state
                if current_state == GPIO.HIGH:
                    self.handle_press(key)
                else:
                    self.handle_release(key)

    def handle_press(self, key):
        if self.current_active_key is not None:
            self.widgets[self.current_active_key].animate_out()

        self.current_active_key = key
        widget = self.widgets[key]
        widget.set_image(self.images[key])
        target_y = self.height() - widget.height()
        target_pos = QPoint(widget.geometry().x(), target_y)
        widget.animate_in(target_pos)

    def handle_release(self, key):
        if key == self.current_active_key:
            self.widgets[key].animate_out()
            self.current_active_key = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        positions = self.calculate_widget_properties()
        for key in SENSOR_PINS.keys():
            widget = self.widgets[key]
            width, height, x, y = positions[key]
            widget.setFixedSize(width, height)
            widget.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
