import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

const componentTests = fileURLToPath(new URL('./tests/components', import.meta.url));
const jsdom = fileURLToPath(import.meta.resolve('jsdom'));
const uiStatic = fileURLToPath(new URL('./src/tavle/static', import.meta.url));

export default defineConfig({
  test: {
    projects: [
      {
        resolve: { alias: { '@ui/static': uiStatic, jsdom } },
        server: { fs: { allow: [componentTests, uiStatic] } },
        test: { name: 'components', root: componentTests, environment: 'jsdom', globals: true, include: ['**/*.test.js'] }
      }
    ]
  }
});
