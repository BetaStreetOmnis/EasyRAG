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
                window: 'readonly',
                document: 'readonly',
                localStorage: 'readonly',
                console: 'readonly',
                setTimeout: 'readonly',
                setInterval: 'readonly',
                fetch: 'readonly',
                Event: 'readonly',
                CustomEvent: 'readonly'
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
                process: 'readonly',
                __dirname: 'readonly',
                __filename: 'readonly',
                console: 'readonly'
            }
        },
        rules: {}
    }
];
