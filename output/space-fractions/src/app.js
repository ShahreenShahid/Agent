const express = require('express');

const app = express();

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'UP', timestamp: new Date().toISOString() });
});

// Game API endpoint aligning with openapi.yaml contract (/play)
app.get('/play', (req, res) => {
  // Mock generating a game ID in compliance with openapi.yaml schema
  const gameId = Math.floor(Math.random() * 1000000);
  res.status(200).json({ gameId });
});

module.exports = app;
