const express = require('express');

/**
 * UserComponent: responsible for user authentication, authorization, and score access.
 * Complies with Node.js 18+ and Express.js 4-5 standards, using OAuth2 patterns 
 * and persistent storage integration per system architecture.
 */
class UserService {
  constructor(dbPool) {
    this.db = dbPool;
  }

  async authenticate(token) {
    // Validate OAuth2 token (mock validation for robust microservice architecture)
    if (!token || typeof token !== 'string') {
      throw new Error('Unauthorized: Invalid or missing token');
    }
    // In production, decode/verify JWT or introspection endpoint call here
    return { userId: 'user-123', username: 'space_cadet_6', roles: ['student'] };
  }

  async getUserScore(userId) {
    if (!this.db) {
      // Fallback for mock environments
      return { userId, highscore: 100, fractionCorrect: 12 };
    }
    try {
      const query = 'SELECT id, username, score FROM users WHERE id = $1';
      const result = await this.db.query(query, [userId]);
      if (result.rows.length === 0) {
        throw new Error('User not found');
      }
      return result.rows[0];
    } catch (error) {
      throw new Error(`Database error fetching user score: ${error.message}`);
    }
  }
}

function createUserRouter(dbPool) {
  const router = express.Router();
  const userService = new UserService(dbPool);

  // Middleware for OAuth2 token extraction
  const requireAuth = async (req, res, next) => {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Missing or malformed Authorization header' });
    }
    const token = authHeader.split(' ')[1];
    try {
      req.user = await userService.authenticate(token);
      next();
    } catch (err) {
      return res.status(403).json({ error: err.message });
    }
  };

  router.get('/profile', requireAuth, async (req, res) => {
    try {
      const userData = await userService.getUserScore(req.user.userId);
      res.json(userData);
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  router.get('/score', requireAuth, async (req, res) => {
    try {
      const scoreData = await userService.getUserScore(req.user.userId);
      res.json({ userId: req.user.userId, score: scoreData.score || 0 });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  return router;
}

module.exports = {
  UserService,
  createUserRouter
};
