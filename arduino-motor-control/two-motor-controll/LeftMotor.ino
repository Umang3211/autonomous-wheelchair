  /* 
(Joystick)
left  pin A1
right pin A0
up    pin A3
down  pin A2

(Left Motor)
pin 13 
pin 12
pin 11
pin 10

*/

int leftpin = A1;
int rightpin = A0;
int uppin = A3;
int downpin = A2;

int leftvalue = 0;
int rightvalue = 0;
int upvalue = 0;
int downvalue = 0;

#include <Stepper.h>
const int stepsPerRevolution = 150;
Stepper leftStepper(stepsPerRevolution, 13, 12, 11, 10);

void setup() {
pinMode(leftpin,INPUT_PULLUP);
pinMode(rightpin,INPUT_PULLUP);
pinMode(uppin,INPUT_PULLUP);
pinMode(downpin,INPUT_PULLUP);

leftStepper.setSpeed(120);

Serial.begin(9600);
}
void setStepperIdle() { 
  digitalWrite(10, LOW);
  digitalWrite(11, LOW);
  digitalWrite(12, LOW);
  digitalWrite(13, LOW);

}

void loop() {
leftvalue = digitalRead(leftpin);
rightvalue = digitalRead(rightpin);
upvalue = digitalRead(uppin);
downvalue = digitalRead(downpin);


if(leftvalue == LOW){
  leftStepper.step(-stepsPerRevolution);
  setStepperIdle();
  Serial.print("left");
  delay(10);}
if(rightvalue == LOW){
  leftStepper.step(stepsPerRevolution);
  setStepperIdle();
  Serial.print("right");
  delay(10);}
if(upvalue == LOW){
  leftStepper.step(stepsPerRevolution);
  setStepperIdle();
  Serial.print("up");
  delay(10);}
if(downvalue == LOW){
  leftStepper.step(-stepsPerRevolution);
  setStepperIdle();
  Serial.print("down");
  delay(10);}


}
