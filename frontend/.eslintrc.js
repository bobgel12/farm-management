/**
 * CRA-compatible ESLint root config. Extends react-app so `react-scripts build`
 * and `npm run lint` behave the same.
 */
module.exports = {
  root: true,
  extends: ['react-app', 'react-app/jest'],
  rules: {
    'no-console': 'off',
    'react-hooks/exhaustive-deps': 'off',
  },
  overrides: [
    {
      files: ['**/*.ts', '**/*.tsx'],
      rules: {
        'no-unused-vars': 'off',
        '@typescript-eslint/no-unused-vars': 'off',
      },
    },
    {
      files: ['**/*.js', '**/*.jsx'],
      rules: {
        'no-unused-vars': 'off',
      },
    },
  ],
};
