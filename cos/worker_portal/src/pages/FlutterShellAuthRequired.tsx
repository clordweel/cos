/** 企业 App WebView 内未携带有效 Portal 令牌时的说明页（勿跳转 Frappe 网页登录）。 */
export function FlutterShellAuthRequired({ attemptedPath }: { attemptedPath: string }) {
	return (
		<div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6 text-center bg-muted/30">
			<p className="text-lg font-semibold">无法验证登录状态</p>
			<p className="text-sm text-muted-foreground max-w-md leading-relaxed">
				当前在企业 App 内打开本业务页，但未携带有效令牌或令牌已失效。请返回应用首页后重新进入本小程序；若反复出现，请检查网络与服务器地址，或联系管理员。
			</p>
			<p className="text-xs text-muted-foreground break-all">路径：{attemptedPath}</p>
		</div>
	)
}
