import path from 'node:path';
import { defineConfig } from 'vite';

export default defineConfig({
    root: '.',
    base: './',
    server: {
        host: '0.0.0.0',
        port: 5173
    },
    build: {
        outDir: '../dist/frontend',
        emptyOutDir: false,
        cssCodeSplit: true,
        rollupOptions: {
            input: './index.html',
            output: {
                entryFileNames: 'script.js',
                chunkFileNames: 'js/[name]-[hash].js',
                assetFileNames: assetInfo => {
                    const fileName = assetInfo.name ?? '';
                    if (/\.(css|woff2?|ttf|eot|svg)$/.test(fileName)) {
                        return '[name][extname]';
                    }
                    return 'assets/[name]-[hash][extname]';
                },
                manualChunks: id => {
                    if (id.includes('node_modules')) {
                        return 'vendor';
                    }
                    return undefined;
                }
            }
        }
    }
});
