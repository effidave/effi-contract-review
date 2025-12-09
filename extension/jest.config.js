module.exports = {
  testEnvironment: 'node',
  testMatch: [
    '**/src/__tests__/**/*.test.js',
    '**/src/__tests__/**/*.test.ts',
    // Include plan.test.js and markdown.test.js from webview/__tests__
    '**/src/webview/__tests__/plan.test.js',
    '**/src/webview/__tests__/markdown.test.js',
    // Exclude the custom runner test file from webview/__tests__
    '!**/src/webview/__tests__/comments.test.js'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    // The comments.test.js uses a custom test runner, not Jest
    '/src/webview/__tests__/comments.test.js'
  ],
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: 'tsconfig.json'
    }]
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  verbose: true
};
