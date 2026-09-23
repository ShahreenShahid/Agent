const express = require('express');
const path = require('path');

const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

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

if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Space Fractions Game server running at http://localhost:${PORT}`);
  });
}
