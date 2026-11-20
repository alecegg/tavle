import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

const componentTests = fileURLToPath(new URL('../components', import.meta.url));
const jsdom = fileURLToPath(import.meta.resolve('jsdom'));
const pagesStatic = fileURLToPath(new URL('../../../src/varde/pages/static', import.meta.url));

export default defineConfig({
  test: {
    projects: [
      {
        resolve: { alias: { '@varde/pages-static': pagesStatic, jsdom } },
        server: { fs: { allow: [componentTests, pagesStatic] } },
        test: { name: 'components', root: componentTests, environment: 'jsdom', globals: true, include: ['**/*.test.js'] }
      }
    ]
  }
});
