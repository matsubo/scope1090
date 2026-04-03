import { defineConfig } from 'vite';

export default defineConfig({
    server: {
        proxy: {
            '/scope1090/api': 'http://127.0.0.1:5000',
        },
    },
    base: '/scope1090/',
    build: {
        outDir: 'dist',
        emptyOutDir: true,
    },
});
