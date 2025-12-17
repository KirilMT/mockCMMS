module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src/static/js/', '<rootDir>/tests/js/'],
  testMatch: ['**/*.test.js'],
  transform: {
    '^.+\\.js$': 'babel-jest',
  },
  collectCoverageFrom: [
    'src/static/js/**/*.js',
    '!src/static/js/**/*.test.js',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
