module.exports = {
    env: {
      browser: true,
      es2021: true,
      node: true, 
    },
    extends: [
      'eslint:recommended',            // 기본 eslint 권장 규칙
      'plugin:react/recommended',      // React 규칙
      'plugin:prettier/recommended',   // Prettier 규칙
      'prettier',                      // prettier-config를 적용하여 prettier와 eslint 충돌을 방지
    ],
    parserOptions: {
      ecmaVersion: 12,
      sourceType: 'module',
      ecmaFeatures: {
        jsx: true,
      },
    },
    plugins: ['react', 'prettier'],
    rules: {
      // 추가적인 ESLint 규칙을 여기에 작성할 수 있습니다
      "no-unused-vars": "warn",
      'prettier/prettier': ['error', { singleQuote: true }], // Prettier 규칙을 강제로 적용
    },
    globals: {
      __dirname: true,  // __dirname을 readonly 전역 변수로 추가
    },
};
  