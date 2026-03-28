import { cn } from "@/lib/utils"

/** 全页浅灰底 + 内容区（与 shadcn Card 边距对齐） */
export function WpPage({
	children,
	className,
	narrow,
}: {
	children: React.ReactNode
	className?: string
	/** 单列表单 / 结果页 */
	narrow?: boolean
}) {
	return (
		<div className={cn("min-h-screen bg-muted/30", className)}>
			<div
				className={cn(
					"mx-auto w-full px-4 pb-8 pt-4 space-y-4",
					narrow ? "max-w-md" : "max-w-2xl",
				)}
			>
				{children}
			</div>
		</div>
	)
}

/** 登录等居中页 */
export function WpAuthPage({ children }: { children: React.ReactNode }) {
	return (
		<div className="min-h-screen bg-muted/30 flex items-center justify-center p-4">
			<div className="w-full max-w-md">{children}</div>
		</div>
	)
}

/** 全屏居中（加载中、短提示） */
export function WpCentered({ children }: { children: React.ReactNode }) {
	return (
		<div className="min-h-screen bg-muted/30 flex items-center justify-center px-4 py-8">
			{children}
		</div>
	)
}

/** 页面主标题（仅浏览器独立访问时使用；嵌入 App WebView 时不渲染，避免与壳顶栏重复） */
export function WpPageTitle({
	children,
	className,
}: {
	children: React.ReactNode
	className?: string
}) {
	return (
		<h1
			className={cn(
				"text-lg font-semibold tracking-tight text-foreground",
				className,
			)}
		>
			{children}
		</h1>
	)
}

/** 统一正文层级（Tailwind + shadcn 语义色） */
export const wpText = {
	body: "text-sm leading-relaxed text-foreground",
	muted: "text-sm leading-relaxed text-muted-foreground",
	caption: "text-xs leading-relaxed text-muted-foreground",
	error: "text-sm text-destructive",
} as const
