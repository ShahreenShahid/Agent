class GameComponent {
  constructor() {
    this.gameState = {
      gameId: null,
      score: 0,
      status: 'IDLE', // IDLE, PLAYING, PAUSED, GAMEOVER
      currentQuestion: null
    };
  }

  async play(gameId) {
    this.gameState.gameId = gameId;
    this.gameState.status = 'PLAYING';
    this.gameState.score = 0;
    return {
      gameId: this.gameState.gameId,
      status: this.gameState.status,
      score: this.gameState.score
    };
  }

  pause() {
    if (this.gameState.status === 'PLAYING') {
      this.gameState.status = 'PAUSED';
    }
    return this.gameState.status;
  }

  resume() {
    if (this.gameState.status === 'PAUSED') {
      this.gameState.status = 'PLAYING';
    }
    return this.gameState.status;
  }

  gameOver() {
    this.gameState.status = 'GAMEOVER';
    return {
      status: this.gameState.status,
      finalScore: this.gameState.score
    };
  }

  submitAnswer(isCorrect, points = 10) {
    if (this.gameState.status !== 'PLAYING') {
      throw new Error('Game is not currently active.');
    }

    if (isCorrect) {
      this.gameState.score += points;
    }

    return {
      score: this.gameState.score,
      isCorrect
    };
  }

  getScore() {
    return this.gameState.score;
  }

  getState() {
    return { ...this.gameState };
  }
}

module.exports = GameComponent;
