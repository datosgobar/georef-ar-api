// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightOpenAPI, { createOpenAPISidebarGroup } from 'starlight-openapi';
import starlightVersions from 'starlight-versions';

// Referencia de cada versión de la API, generada desde su spec (los archivos también se pueden descargar).
const referencia = createOpenAPISidebarGroup();
const referenciaV1 = createOpenAPISidebarGroup();

const base = '/georef-ar-api';

export default defineConfig({
	site: 'https://datosgobar.github.io',
	base,
	trailingSlash: 'ignore',
	redirects: {
		// El visor Swagger se reemplazó por la referencia generada.
		'/open-api/': `${base}/referencia/`,
	},
	integrations: [
		starlight({
			plugins: [
				// La documentación actual es la de la API v2.1; la de v1.0 queda archivada en /v1/ con aviso de versión anterior.
				starlightVersions({ current: { label: 'v2.1 (actual)' }, versions: [{ slug: 'v1', label: 'v1.0 (deprecada)' }] }),
				starlightOpenAPI([
					{ base: 'referencia', schema: './public/openapi.json', sidebar: { label: 'Referencia API', group: referencia, operations: { badges: true, labels: 'path' } } },
					{ base: 'v1/referencia', schema: './public/openapi-v1.0.json', sidebar: { label: 'Referencia API', group: referenciaV1, operations: { badges: true, labels: 'path' } } },
					// ponytail: el menú archivado (src/content/versions/v1.json) enlaza a mano a /referencia/, que el plugin prefija con /v1/; este grupo no se muestra.
				]),
			],
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
						{ label: 'Migrar desde v1.0', slug: 'migrar-desde-v1' },
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
								{ label: 'Gobiernos locales', slug: 'gobiernos-locales' },
								{ label: 'Comunas de CABA', slug: 'communes' },
								{ label: 'Entidades censales y establecimientos', slug: 'entidades-censales-y-establecimientos' },
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
