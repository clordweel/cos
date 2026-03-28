import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { WpAuthPage, wpText } from "@/lib/wp-layout"

/** 企业 App WebView 内未携带有效 Portal 令牌时的说明页（勿跳转 Frappe 网页登录）。 */
export function FlutterShellAuthRequired({ attemptedPath }: { attemptedPath: string }) {
	return (
		<WpAuthPage>
			<Card className="w-full text-center">
				<CardHeader>
					<CardTitle className="text-lg">无法验证登录状态</CardTitle>
				</CardHeader>
				<CardContent className="space-y-3">
					<p className={wpText.muted}>
						请返回应用首页后重新进入；若反复出现，请检查网络与服务器地址。
					</p>
					<p className={cn(wpText.caption, "break-all")}>{attemptedPath}</p>
				</CardContent>
			</Card>
		</WpAuthPage>
	)
}
