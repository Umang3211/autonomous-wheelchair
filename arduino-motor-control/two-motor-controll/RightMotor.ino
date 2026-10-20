  /* 
(Joystick)
left  pin A1
right pin A0
up    pin A3
down  pin A2

(Right Motor)
pin 13 
pin 12
pin 11
pin 10

*/

int leftpin = A5;
int rightpin = A2;
int uppin = A0;
int downpin = A4;

int leftvalue = 0;
int rightvalue = 0;
int upvalue = 0;
int downvalue = 0;

#include <Stepper.h>
const int stepsPerRevolution = 150;
Stepper rightStepper(stepsPerRevolution, 2, 3, 4, 5);

void setup() {
pinMode(leftpin,INPUT_PULLUP);
pinMode(rightpin,INPUT_PULLUP);
pinMode(uppin,INPUT_PULLUP);
pinMode(downpin,INPUT_PULLUP);

rightStepper.setSpeed(120);

Serial.begin(9600);
}
void setStepperIdle() { 
  digitalWrite(2, LOW);
  digitalWrite(3, LOW);
  digitalWrite(4, LOW);
  digitalWrite(5, LOW);

}

void loop() {
leftvalue = digitalRead(leftpin);
rightvalue = digitalRead(rightpin);
upvalue = digitalRead(uppin);
downvalue = digitalRead(downpin);

if(leftvalue == LOW){
  rightStepper.step(stepsPerRevolution);
  setStepperIdle();
  Serial.print("left");
  delay(10);}
if(rightvalue == LOW){
  rightStepper.step(-stepsPerRevolution);
  setStepperIdle();
  Serial.print("right");
  delay(10);}
if(upvalue == LOW){
  rightStepper.step(stepsPerRevolution);
  setStepperIdle();
  Serial.print("up");
  delay(10);}
if(downvalue == LOW){
  rightStepper.step(-stepsPerRevolution); 
  setStepperIdle();
  Serial.print("down");
  delay(10);}


}
