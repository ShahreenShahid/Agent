const express = require('express');
const { Pool } = require('pg');

const router = express.Router();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/spacefractions'
});

router.get('/questions/:id', async (req, res) => {
  const { id } = req.params;
  try {
    const result = await pool.query('SELECT id, prompt, options, answer FROM questions WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Question not found' });
    }
    const question = result.rows.id;
    // Hide the correct answer from the client when retrieving the prompt
    res.json({
      id: question.id,
      prompt: question.prompt,
      options: question.options
    });
  } catch (err) {
    console.error('Error retrieving question:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/questions/:id/check', async (req, res) => {
  const { id } = req.params;
  const { answer } = req.body;

  if (answer === undefined) {
    return res.status(400).json({ error: 'Answer is required' });
  }

  try {
    const result = await pool.query('SELECT answer FROM questions WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Question not found' });
    }

    const correctAnswer = result.rows.answer;
    const isCorrect = String(correctAnswer).trim() === String(answer).trim();

    res.json({ correct: isCorrect });
  } catch (err) {
    console.error('Error checking answer:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
