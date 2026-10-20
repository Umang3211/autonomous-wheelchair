/*
Buttons (same style as your LeftMotor.ino comment):
LEFT  -> A1
RIGHT -> A0
UP    -> A3
DOWN  -> A2

TB6600 wiring (typical):
Left driver:  DIR -> D2, STEP -> D3
Right driver: DIR -> D4, STEP -> D5

If you are using ENA on TB6600:
- You can leave ENA always enabled via wiring (common setup), or
- Uncomment ENABLE pins and wire them.

Behavior:
- UP: forward
- DOWN: backward
- LEFT: spin left
- RIGHT: spin right
- UP+LEFT / UP+RIGHT: arc turns (one side slower)
- DOWN+LEFT / DOWN+RIGHT: arc turns backwards
*/

const int BTN_LEFT  = A1;
const int BTN_RIGHT = A0;
const int BTN_UP    = A3;
const int BTN_DOWN  = A2;

// Motor pins
const int DIR_L  = 2;
const int STEP_L = 3;

const int DIR_R  = 4;
const int STEP_R = 5;

// Optional enable pins (uncomment if you wired ENA to Arduino pins)
// const int EN_L = 8;
// const int EN_R = 9;
// const bool EN_ACTIVE_LOW = true;

// If one motor direction is flipped, change these:
const bool INVERT_LEFT_DIR  = false;
const bool INVERT_RIGHT_DIR = false;

// Speed control: half-period in microseconds.
// Smaller = faster. Start conservative.
const unsigned int BASE_HALF_PERIOD_US = 500;   // ~1000 step pulses/sec if toggling
const unsigned int TURN_HALF_PERIOD_US = 500;   // spin speed
const unsigned int SLOW_HALF_PERIOD_US = 800;   // slower wheel for arc turns

struct StepperPulse {
  int stepPin;
  int dirPin;

  bool active = false;
  bool dirForward = true;

  unsigned int halfPeriodUs = BASE_HALF_PERIOD_US;
  bool stepState = false;
  unsigned long lastToggleUs = 0;
};

StepperPulse leftMotor  = {STEP_L, DIR_L};
StepperPulse rightMotor = {STEP_R, DIR_R};

void setMotor(StepperPulse &m, bool active, bool forward, unsigned int halfPeriod) {
  m.active = active;
  m.dirForward = forward;
  m.halfPeriodUs = halfPeriod;

  // Apply direction (with optional invert)
  bool dirLevel = forward ? HIGH : LOW;
  if (m.dirPin == DIR_L && INVERT_LEFT_DIR)  dirLevel = (dirLevel == HIGH) ? LOW : HIGH;
  if (m.dirPin == DIR_R && INVERT_RIGHT_DIR) dirLevel = (dirLevel == HIGH) ? LOW : HIGH;

  digitalWrite(m.dirPin, dirLevel);
}

void stopMotor(StepperPulse &m) {
  m.active = false;
  m.stepState = false;
  digitalWrite(m.stepPin, LOW);
}

void updateMotor(StepperPulse &m) {
  if (!m.active) return;

  unsigned long now = micros();
  if (now - m.lastToggleUs >= m.halfPeriodUs) {
    m.lastToggleUs = now;
    m.stepState = !m.stepState;
    digitalWrite(m.stepPin, m.stepState ? HIGH : LOW);
  }
}

void setup() {
  pinMode(BTN_LEFT,  INPUT_PULLUP);
  pinMode(BTN_RIGHT, INPUT_PULLUP);
  pinMode(BTN_UP,    INPUT_PULLUP);
  pinMode(BTN_DOWN,  INPUT_PULLUP);

  pinMode(DIR_L, OUTPUT);
  pinMode(STEP_L, OUTPUT);
  pinMode(DIR_R, OUTPUT);
  pinMode(STEP_R, OUTPUT);

  // Optional enable pins
  // pinMode(EN_L, OUTPUT);
  // pinMode(EN_R, OUTPUT);
  // digitalWrite(EN_L, EN_ACTIVE_LOW ? LOW : HIGH);
  // digitalWrite(EN_R, EN_ACTIVE_LOW ? LOW : HIGH);

  Serial.begin(115200);
  Serial.println("Dual TB6600 drive test starting...");
}

void loop() {
  // Buttons are ACTIVE LOW (pressed = LOW)
  bool left  = (digitalRead(BTN_LEFT)  == LOW);
  bool right = (digitalRead(BTN_RIGHT) == LOW);
  bool up    = (digitalRead(BTN_UP)    == LOW);
  bool down  = (digitalRead(BTN_DOWN)  == LOW);

  // Default: stop
  bool any = left || right || up || down;
  if (!any) {
    stopMotor(leftMotor);
    stopMotor(rightMotor);
  } else {
    // Priority: arc turns if combined with up/down
    if (up && left) {
      // Forward + slight left (left slower, right normal)
      setMotor(leftMotor,  true,  true,  SLOW_HALF_PERIOD_US);
      setMotor(rightMotor, true,  true,  BASE_HALF_PERIOD_US);
    } else if (up && right) {
      // Forward + slight right
      setMotor(leftMotor,  true,  true,  BASE_HALF_PERIOD_US);
      setMotor(rightMotor, true,  true,  SLOW_HALF_PERIOD_US);
    } else if (down && left) {
      // Backward + slight left
      setMotor(leftMotor,  true,  false, SLOW_HALF_PERIOD_US);
      setMotor(rightMotor, true,  false, BASE_HALF_PERIOD_US);
    } else if (down && right) {
      // Backward + slight right
      setMotor(leftMotor,  true,  false, BASE_HALF_PERIOD_US);
      setMotor(rightMotor, true,  false, SLOW_HALF_PERIOD_US);
    } else if (up) {
      // Straight forward
      setMotor(leftMotor,  true, true, BASE_HALF_PERIOD_US);
      setMotor(rightMotor, true, true, BASE_HALF_PERIOD_US);
    } else if (down) {
      // Straight backward
      setMotor(leftMotor,  true, false, BASE_HALF_PERIOD_US);
      setMotor(rightMotor, true, false, BASE_HALF_PERIOD_US);
    } else if (left) {
      // Spin left in place: left backward, right forward
      setMotor(leftMotor,  true, false, TURN_HALF_PERIOD_US);
      setMotor(rightMotor, true, true,  TURN_HALF_PERIOD_US);
    } else if (right) {
      // Spin right in place
      setMotor(leftMotor,  true, true,  TURN_HALF_PERIOD_US);
      setMotor(rightMotor, true, false, TURN_HALF_PERIOD_US);
    }
  }

  // Keep generating step pulses (non-blocking)
  updateMotor(leftMotor);
  updateMotor(rightMotor);
}
