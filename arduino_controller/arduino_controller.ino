#include <Servo.h>
#include <Keypad.h>
#define echoPin 12 // attach pin D2 Arduino to pin Echo of HC-SR04
#define trigPin 13//attach pin D3 Arduino to pin Trig of HC-SR04
#define redled 10
//#define greenled 0
// defines variables
long duration; // variable for the duration of sound wave travel
int distance; // variable for the distance measurement

const byte numRows= 4; //number of rows on the keypad
const byte numCols= 4; //number of columns on the keypad

//keymap defines the key pressed according to the row and columns just as appears on the keypad
char keymap[numRows][numCols]=
{
{'1', '2', '3', 'A'},
{'4', '5', '6', 'B'},
{'7', '8', '9', 'C'},
{'*', '0', '#', 'D'}
};

//Code that shows the the keypad connections to the arduino terminals
byte rowPins[numRows] = {9,8,7,6}; //Rows 0 to 3
byte colPins[numCols]= {5,4,3,2}; //Columns 0 to 3

//initializes an instance of the Keypad class
Keypad myKeypad= Keypad(makeKeymap(keymap), rowPins, colPins, numRows, numCols);

int inByte = 0;         // incoming serial byte
Servo myservo;  // create servo object to control a servo

void setup()
{
Serial.begin(9600);
 myservo.attach(11);
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an OUTPUT
  pinMode(echoPin, INPUT); // Sets the echoPin as an INPUT
  pinMode(redled, OUTPUT);
  //pinMode(greenled, OUTPUT);
  //digitalWrite(redled,HIGH);
}

//If key is pressed, this key is stored in 'keypressed' variable
//If key is not equal to 'NO_KEY', then this key is printed out

void loop()
{

  if (Serial.available() > 0) {
    // get incoming byte:
    int val = char(Serial.read())-'0';
//    Serial.println(val);
//    Serial.write("\n");
    if(val == 1){
      myservo.write(170);     // sets the servo position according to the scaled value
       //digitalWrite(greenled, HIGH);
       digitalWrite(redled,LOW);
       delay(4000);
         
       myservo.write(0);
       //digitalWrite(greenled,LOW);
        digitalWrite(redled,HIGH);
       delay(1000);
      } 
    if(val == 2 ){
       // Clears the trigPin condition
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin HIGH (ACTIVE) for 10 microseconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  // Calculating the distance
  distance = duration * 0.034 / 2; // Speed of sound wave divided by 2 (go and back)
  Serial.print(distance);
      }    
                               }
 
char keypressed = myKeypad.getKey();
if (keypressed != NO_KEY)
{
Serial.print(keypressed);
}
}
