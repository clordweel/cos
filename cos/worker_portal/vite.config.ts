import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"

export default defineConfig({
	plugins: [react()],
	resolve: {
		alias: { "@": path.resolve(__dirname, "./src") },
	},
	build: {
		outDir: "../public/worker_portal",
		emptyOutDir: true,
		cssCodeSplit: false,
		rollupOptions: {
			input: path.resolve(__dirname, "index.html"),
			output: {
				entryFileNames: "worker-portal.js",
				chunkFileNames: "worker-portal-[name].js",
				assetFileNames: (info) =>
					info.name?.endsWith(".css") ? "worker-portal.css" : "worker-portal-[name][extname]",
			},
		},
	},
})
