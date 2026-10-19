// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { satteri } from '@astrojs/markdown-satteri';
import starlightOpenAPI, { createOpenAPISidebarGroup } from 'starlight-openapi';

// Páginas de referencia generadas desde public/openapi.json (el mismo archivo se puede descargar).
const referencia = createOpenAPISidebarGroup();

// Mismos ids de encabezado que generaba mkdocs (toc.slugify): sin tildes.
// Así siguen funcionando los #anclas enlazados desde afuera. Igual que en series-tiempo-ar-api y paquete-apertura-datos.
const mkdocsSlugs = () => {
	const seen = new Map();
	return {
		name: 'mkdocs-slugs',
		element: {
			filter: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
			visit(node, ctx) {
				if (typeof node.properties?.id === 'string') return;
				let id = ctx.textContent(node).normalize('NFKD').replace(/[^\x00-\x7F]/g, '')
					.replace(/[^\w\s-]/g, '').trim().toLowerCase().replace(/[-\s]+/g, '-');
				const k = seen.get(id) ?? 0;
				seen.set(id, k + 1);
				ctx.setProperty(node, 'id', k ? `${id}_${k}` : id);
			},
		},
	};
};

const base = '/georef-ar-api';

export default defineConfig({
	site: 'https://datosgobar.github.io',
	base,
	trailingSlash: 'ignore',
	markdown: { processor: satteri({ hastPlugins: [mkdocsSlugs] }) },
	redirects: {
		// El visor Swagger se reemplazó por la referencia generada.
		'/open-api/': `${base}/referencia/`,
		// La página de Python 3.6 no se migró; su contenido vigente está en Usar en Python.
		'/python3.6/': `${base}/python-usage/`,
		// Páginas que mkdocs seguía sirviendo desde docs/ aunque ya no tenían fuente.
		'/open-api/src/': `${base}/referencia/`,
		'/georef-api-data/': `${base}/etl-data/`,
		'/municipalities/': `${base}/localities/`,
	},
	integrations: [
		starlight({
			plugins: [starlightOpenAPI([{ base: 'referencia', schema: './public/openapi.json', sidebar: { label: 'Referencia API', group: referencia, operations: { badges: true, labels: 'path' } } }])],
			title: 'API Georef',
			favicon: '/favicon.png',
			description: 'Documentación de la API del Servicio de Normalización de Datos Geográficos de la República Argentina.',
			defaultLocale: 'root',
			locales: { root: { label: 'Español', lang: 'es' } },
			customCss: ['./src/styles/datos.css', './src/styles/georef.css'],
			components: { Header: './src/components/Cabecera.astro' },
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/datosgobar/georef-ar-api' }],
			editLink: { baseUrl: 'https://github.com/datosgobar/georef-ar-api/edit/master/' },
			head: [
				{ tag: 'link', attrs: { rel: 'preconnect', href: 'https://fonts.googleapis.com' } },
				{ tag: 'link', attrs: { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true } },
				{ tag: 'link', attrs: { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap' } },
			],
			// Mismo menú que el nav de mkdocs.yml, sin la página de Python 3.6.
			sidebar: [
				{ label: 'Inicio', link: '/' },
				{
					label: 'Usuarios',
					items: [
						{ label: 'Ejemplos de uso', slug: 'quick-start' },
						{ label: 'Consultas por lotes', slug: 'bulk' },
						{ label: 'Normalización de direcciones', slug: 'addresses' },
						{ label: 'Operaciones con geometrías', slug: 'geom-operations' },
						{ label: 'Descarga de geometrías', slug: 'shapefiles' },
						{ label: 'Descarga de base completa', slug: 'download' },
						{ label: 'Usar en planillas de cálculo', slug: 'spreadsheet-integration' },
						{ label: 'Usar en Python', slug: 'python-usage' },
						{ label: 'Autenticarse con JWT', slug: 'jwt-token' },
						referencia,
						{
							label: 'Referencia metodológica',
							items: [
								{ label: 'Comunas de CABA', slug: 'communes' },
								{ label: 'Localidades y asentamientos', slug: 'localities' },
							],
						},
						{ label: 'Condiciones de uso', slug: 'terms' },
					],
				},
				{ label: 'Aplicaciones', slug: 'applications' },
				{
					label: 'Desarrolladores',
					items: [
						{ label: 'Instalación y ejecución', slug: 'georef-api-development' },
						{ label: 'Entornos productivos', slug: 'deploy' },
						{ label: 'Historial de versiones', slug: 'history' },
						{
							label: 'ETL',
							items: [
								{ label: 'Inicio', slug: 'etl' },
								{ label: 'Datos', slug: 'etl-data' },
								{ label: 'Instalación y ejecución', slug: 'etl-install' },
							],
						},
					],
				},
			],
		}),
	],
});
