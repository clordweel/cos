import globals from "globals"
import tseslint from "typescript-eslint"

/**
 * 仅启用壳顶占位相关约束 + TS/JSX 解析；不拉满 recommended，避免与既有代码风格冲突。
 */
export default tseslint.config(
	{ ignores: ["../public/worker_portal/**", "node_modules/**"] },
	{
		files: ["src/**/*.{ts,tsx}"],
		languageOptions: {
			parser: tseslint.parser,
			parserOptions: {
				ecmaVersion: 2022,
				sourceType: "module",
				ecmaFeatures: { jsx: true },
			},
			globals: globals.browser,
		},
		plugins: { "@typescript-eslint": tseslint.plugin },
	},
	{
		files: ["src/**/*.{ts,tsx}"],
		ignores: ["src/lib/clientEnv.ts"],
		rules: {
			"no-restricted-syntax": [
				"error",
				{
					selector: "Literal[value=/--cos-content-padding-top/]",
					message:
						"禁止手写 --cos-content-padding-top 壳顶 var：请使用 @/lib/clientEnv 的 COS_SHELL_CONTENT_PADDING_TOP_CSS 或 cosFlutterShellContentInsetStyle()。",
				},
				{
					selector: "TemplateElement[value.raw=/--cos-content-padding-top/]",
					message:
						"禁止在模板字符串中手写 --cos-content-padding-top：请使用 COS_SHELL_CONTENT_PADDING_TOP_CSS 或 cosFlutterShellContentInsetStyle()。",
				},
			],
		},
	},
)
