import { defineCollection } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';
import { docsVersionsLoader } from 'starlight-versions/loader';

export const collections = {
	docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }),
	// Menú de cada versión archivada (src/content/versions/<versión>.json), lo genera starlight-versions.
	versions: defineCollection({ loader: docsVersionsLoader() }),
};
