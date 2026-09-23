const request = require('supertest');
const app = require('../src/app');

describe('Space Fractions API Tests', () => {
  test('GET /play should return game started response with gameId', async () => {
    const response = await request(app).get('/play');
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('gameId');
    expect(typeof response.body.gameId).toBe('number');
  });

  test('GET /health should return system health status', async () => {
    const response = await request(app).get('/health');
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('status', 'UP');
  });
});
