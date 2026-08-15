import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
    use: {
        baseURL: 'http://127.0.0.1:4173',
        headless: true,
    },
    webServer: {
        command: 'test -f dist/frontend/index.html && npm run preview -- --host 127.0.0.1 --port 4173 --strictPort',
        url: 'http://127.0.0.1:4173/',
        reuseExistingServer: true,
    },
});
