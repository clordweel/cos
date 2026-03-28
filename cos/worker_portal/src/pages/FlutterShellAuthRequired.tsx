import { WpEmptyState } from "@/components/wp-states"
import { KeyRound } from "lucide-react"
import { cn } from "@/lib/utils"
import { WpAuthPage, wpText } from "@/lib/wp-layout"

/** 企业 App WebView 内未携带有效 Portal 令牌时的说明页（勿跳转 Frappe 网页登录）。 */
export function FlutterShellAuthRequired({ attemptedPath }: { attemptedPath: string }) {
	return (
		<WpAuthPage>
			<WpEmptyState
				icon={KeyRound}
				title="无法验证登录状态"
				description="请在企业 App 内从首页重新进入本功能；若反复出现，请检查网络与服务器地址。"
			>
				<p className={cn(wpText.caption, "break-all text-left w-full")}>{attemptedPath}</p>
			</WpEmptyState>
		</WpAuthPage>
	)
}
