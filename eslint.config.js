import globals from 'globals';

export default [
    {
        ignores: ['dist/**', 'node_modules/**']
    },
    {
        files: ['static/**/*.js'],
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            globals: {
                ...globals.browser
            }
        },
        rules: {}
    },
    {
        files: ['vite.config.js'],
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            globals: {
                ...globals.node
            }
        },
        rules: {}
    }
];
