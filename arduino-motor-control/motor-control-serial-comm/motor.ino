/*
Dual TB6600 Step/Dir + Manual Override + Serial Commands

Manual controls (4-button joystick, active LOW):
LEFT  -> A1
RIGHT -> A0
UP    -> A3
DOWN  -> A2

Motors:
Left  TB6600: DIR_L=2, STEP_L=3
Right TB6600: DIR_R=4, STEP_R=5

Serial protocol (newline-terminated):
  AUTO <vL> <vR>
    vL, vR are signed integers = steps/second (approx), e.g. AUTO 1200 1200
  STOP
  PING

Arduino behavior:
- If any joystick button is pressed => MANUAL mode takes over immediately.
- When joystick released => returns to AUTO after a short "release delay".
- If AUTO command not received for SERIAL_TIMEOUT_MS => stops (unless manual active).
*/

#include <Arduino.h>

// ----- Joystick buttons (active LOW)
const int BTN_LEFT  = A1;
const int BTN_RIGHT = A0;
const int BTN_UP    = A3;
const int BTN_DOWN  = A2;

// ----- Motor pins
const int DIR_L  = 2;
const int STEP_L = 3;
const int DIR_R  = 4;
const int STEP_R = 5;

// If one motor direction is flipped, toggle these:
const bool INVERT_LEFT_DIR  = false;
const bool INVERT_RIGHT_DIR = false;

// ----- Limits / tuning
const int MAX_STEPS_PER_SEC = 6000;      // clamp safety
const int MIN_STEPS_PER_SEC = 50;        // below this, treat as stop (prevents stutter)

// Manual speeds (steps/sec)
const int MANUAL_FWD  = 2000;
const int MANUAL_TURN = 1800;

// Timeouts
const unsigned long SERIAL_TIMEOUT_MS   = 250;   // stop if no AUTO cmd arrives
const unsigned long MANUAL_RELEASE_MS   = 250;   // after joystick release, wait before returning to auto
const unsigned long STATUS_PERIOD_MS    = 250;   // how often we print status

// ----- Motor pulse generator (non-blocking)
struct StepperPulse {
  int stepPin;
  int dirPin;

  bool active = false;
  bool dirForward = true;          // true=forward, false=reverse
  int stepsPerSec = 0;             // signed, but active direction handled separately

  bool stepState = false;
  unsigned long lastToggleUs = 0;
  unsigned int halfPeriodUs = 0;   // computed from steps/sec
};

StepperPulse L {STEP_L, DIR_L};
StepperPulse R {STEP_R, DIR_R};

static inline int clampInt(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

void setDir(int dirPin, bool forward, bool invertFlag) {
  bool level = forward ? HIGH : LOW;
  if (invertFlag) level = !level;
  digitalWrite(dirPin, level);
}

void setMotorSpeed(StepperPulse &m, int signedStepsPerSec, bool invertDirFlag) {
  // signedStepsPerSec: +forward, -reverse, 0 stop
  if (signedStepsPerSec == 0 || abs(signedStepsPerSec) < MIN_STEPS_PER_SEC) {
    m.active = false;
    m.stepsPerSec = 0;
    m.stepState = false;
    digitalWrite(m.stepPin, LOW);
    return;
  }

  int sps = abs(signedStepsPerSec);
  sps = clampInt(sps, MIN_STEPS_PER_SEC, MAX_STEPS_PER_SEC);

  m.active = true;
  m.stepsPerSec = sps;
  m.dirForward = (signedStepsPerSec > 0);

  setDir(m.dirPin, m.dirForward, invertDirFlag);

  // halfPeriodUs = 1e6 / (2*sps)
  // Using integer math; safe for typical step rates.
  m.halfPeriodUs = (unsigned int)(1000000UL / (2UL * (unsigned long)sps));
  if (m.halfPeriodUs < 2) m.halfPeriodUs = 2; // avoid too-fast toggling
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

// ----- Serial parsing
String rxLine;

unsigned long lastAutoCmdMs = 0;
unsigned long lastStatusMs  = 0;

bool manualActive = false;
unsigned long manualLastPressedMs = 0;

// last commanded AUTO velocities
int autoVL = 0;
int autoVR = 0;

void handleSerialLine(const String &line) {
  // Minimal tokenizer
  // Expected: "AUTO vL vR" or "STOP" or "PING"
  if (line.length() == 0) return;

  if (line.startsWith("PING")) {
    Serial.println("PONG");
    return;
  }

  if (line.startsWith("STOP")) {
    autoVL = 0;
    autoVR = 0;
    lastAutoCmdMs = millis();
    Serial.println("OK STOP");
    return;
  }

  if (line.startsWith("AUTO")) {
    int firstSpace = line.indexOf(' ');
    if (firstSpace < 0) return;

    int secondSpace = line.indexOf(' ', firstSpace + 1);
    if (secondSpace < 0) return;

    String s1 = line.substring(firstSpace + 1, secondSpace);
    String s2 = line.substring(secondSpace + 1);

    int vL = s1.toInt();
    int vR = s2.toInt();

    vL = clampInt(vL, -MAX_STEPS_PER_SEC, MAX_STEPS_PER_SEC);
    vR = clampInt(vR, -MAX_STEPS_PER_SEC, MAX_STEPS_PER_SEC);

    autoVL = vL;
    autoVR = vR;
    lastAutoCmdMs = millis();

    Serial.println("OK AUTO");
    return;
  }

  // Unknown command
  Serial.print("ERR ");
  Serial.println(line);
}

// ----- Manual joystick -> wheel speeds
void computeManual(int &vL, int &vR) {
  // active LOW buttons
  bool left  = (digitalRead(BTN_LEFT)  == LOW);
  bool right = (digitalRead(BTN_RIGHT) == LOW);
  bool up    = (digitalRead(BTN_UP)    == LOW);
  bool down  = (digitalRead(BTN_DOWN)  == LOW);

  vL = 0; vR = 0;

  // Allow combos (arc turns) similar to a real chair
  if (up && left) {
    vL = MANUAL_FWD / 2;
    vR = MANUAL_FWD;
  } else if (up && right) {
    vL = MANUAL_FWD;
    vR = MANUAL_FWD / 2;
  } else if (down && left) {
    vL = -(MANUAL_FWD / 2);
    vR = -MANUAL_FWD;
  } else if (down && right) {
    vL = -MANUAL_FWD;
    vR = -(MANUAL_FWD / 2);
  } else if (up) {
    vL = MANUAL_FWD;
    vR = MANUAL_FWD;
  } else if (down) {
    vL = -MANUAL_FWD;
    vR = -MANUAL_FWD;
  } else if (left) {
    // spin left in place
    vL = -MANUAL_TURN;
    vR =  MANUAL_TURN;
  } else if (right) {
    // spin right in place
    vL =  MANUAL_TURN;
    vR = -MANUAL_TURN;
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

  Serial.begin(115200);
  rxLine.reserve(80);

  lastAutoCmdMs = millis();
  lastStatusMs  = millis();

  Serial.println("READY");
}

void loop() {
  // ---- Read serial lines (non-blocking)
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      rxLine.trim();
      handleSerialLine(rxLine);
      rxLine = "";
    } else if (c != '\r') {
      rxLine += c;
      if (rxLine.length() > 120) rxLine = ""; // simple overflow protection
    }
  }

  // ---- Manual override detection
  bool anyPressed =
    (digitalRead(BTN_LEFT)  == LOW) ||
    (digitalRead(BTN_RIGHT) == LOW) ||
    (digitalRead(BTN_UP)    == LOW) ||
    (digitalRead(BTN_DOWN)  == LOW);

  unsigned long nowMs = millis();

  if (anyPressed) {
    manualActive = true;
    manualLastPressedMs = nowMs;
  } else {
    // If released, keep manual for a short grace period to avoid flicker
    if (manualActive && (nowMs - manualLastPressedMs > MANUAL_RELEASE_MS)) {
      manualActive = false;
    }
  }

  // ---- Decide wheel commands
  int cmdVL = 0, cmdVR = 0;

  if (manualActive) {
    computeManual(cmdVL, cmdVR);
  } else {
    // AUTO mode: stop if serial timed out
    if (nowMs - lastAutoCmdMs > SERIAL_TIMEOUT_MS) {
      cmdVL = 0;
      cmdVR = 0;
    } else {
      cmdVL = autoVL;
      cmdVR = autoVR;
    }
  }

  // ---- Apply to motors
  setMotorSpeed(L, cmdVL, INVERT_LEFT_DIR);
  setMotorSpeed(R, cmdVR, INVERT_RIGHT_DIR);

  // ---- Generate step pulses
  updateMotor(L);
  updateMotor(R);

  // ---- Status output (optional but useful)
  if (nowMs - lastStatusMs > STATUS_PERIOD_MS) {
    lastStatusMs = nowMs;
    Serial.print("STAT ");
    Serial.print(manualActive ? "MANUAL " : "AUTO ");
    Serial.print(cmdVL);
    Serial.print(" ");
    Serial.println(cmdVR);
  }
}
