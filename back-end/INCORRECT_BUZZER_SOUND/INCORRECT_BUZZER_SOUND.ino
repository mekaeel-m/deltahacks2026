const int piezoPin = 8;
const int duration = 300; 
const int frequency = 800;

void setup() {
  Serial.begin(9600);
  pinMode(piezoPin, OUTPUT); 
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (command == "PLAY_TONE") {
      tone(piezoPin, frequency, duration);
      delay(duration);
      noTone(piezoPin);
    }
    Serial.println("OK");
  }
}
