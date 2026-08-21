import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import adapter from '@sveltejs/adapter-auto';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig, type Plugin } from 'vite';

// The brand (accent, gray scale, font stack) is defined once in
// packages/app/src/brand.json — the emails read it directly, the web gets it
// compiled into Tailwind theme tokens here. Regenerates src/brand.css on every
// dev server start and build; the file is committed so svelte-check works alone.
function brandTheme(): Plugin {
	const root = fileURLToPath(new URL('.', import.meta.url));
	const brand: Record<string, string> = JSON.parse(
		readFileSync(`${root}../app/src/brand.json`, 'utf-8')
	);
	const tokens = Object.entries(brand).map(([key, value]) =>
		key === 'font' ? `\t--font-sans: ${value};` : `\t--color-${key.replaceAll('_', '-')}: ${value};`
	);
	writeFileSync(
		`${root}src/brand.css`,
		`/* Generated from packages/app/src/brand.json by vite.config.ts — do not edit. */\n@theme {\n\t--color-gray-*: initial;\n${tokens.join('\n')}\n}\n`
	);
	return { name: 'brand-theme' };
}

export default defineConfig({
	plugins: [
		brandTheme(),
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			// Every route is prerendered (see src/routes/+layout.ts), so on Vercel
			// this emits a purely static site with no server functions.
			adapter: adapter()
		})
	]
});
