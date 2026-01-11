/**
 * Simple Serial Bridge for Arduino Piezo Control
 * Listens on port 3001 for HTTP requests and forwards to Arduino
 * 
 * Install dependencies:
 *   npm install express serialport
 * 
 * Usage:
 *   node serial-server.js
 */

const express = require('express');
const SerialPort = require('serialport').SerialPort;
const app = express();

const PORT = 3001;
const ARDUINO_PORT = 'COM6';  // Change this to your Arduino port (COM3, /dev/ttyUSB0, etc)
const BAUD_RATE = 9600;

let serialPort = null;

// Initialize serial connection
function initializeSerial() {
  serialPort = new SerialPort({
    path: ARDUINO_PORT,
    baudRate: BAUD_RATE,
    autoOpen: true
  });

  serialPort.on('open', () => {
    console.log(`Serial port ${ARDUINO_PORT} opened at ${BAUD_RATE} baud`);
  });

  serialPort.on('error', (err) => {
    console.error('Serial port error:', err.message);
  });

  serialPort.on('close', () => {
    console.log('Serial port closed');
  });
}

// Middleware
app.use(express.json());

// Enable CORS for all routes
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', serialPortOpen: serialPort?.isOpen });
});

// Play tone endpoint
app.post('/play-tone', (req, res) => {
  if (!serialPort || !serialPort.isOpen) {
    return res.status(500).json({ error: 'Serial port not connected' });
  }

  serialPort.write('PLAY_TONE\n', (err) => { // crucial Serial message to Arduino
    if (err) {
      console.error('Write error:', err);
      return res.status(500).json({ error: err.message });
    }
    res.json({ status: 'tone played' });
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Serial bridge listening on http://localhost:${PORT}`);
  initializeSerial();
});
