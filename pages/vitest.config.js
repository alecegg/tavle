import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

const componentTests = fileURLToPath(new URL('./tests/components', import.meta.url));
const pagesStatic = fileURLToPath(new URL('./src/varde_pages/static', import.meta.url));

export default defineConfig({
  test: {
    projects: [
      {
        resolve: { alias: { '@varde/pages-static': pagesStatic } },
        server: { fs: { allow: [componentTests, pagesStatic] } },
        test: { name: 'components', root: componentTests, environment: 'jsdom', globals: true, include: ['**/*.test.js'] }
      }
    ]
  }
});
