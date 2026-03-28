import type { LucideIcon } from "lucide-react"
import {
	AlertCircle,
	CheckCircle2,
	Inbox,
	KeyRound,
	Link2Off,
	Loader2,
	SearchX,
	ShieldAlert,
	WifiOff,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import {
	classifyWorkerPortalError,
	type WpErrorKind,
} from "@/lib/wp-error-kind"
import { wpText } from "@/lib/wp-layout"

/** 全屏居中容器内使用（与 WpCentered / WpAuthPage 搭配） */
export function WpLoadingState({ label = "加载中…" }: { label?: string }) {
	return (
		<div className="flex flex-col items-center justify-center gap-3 py-6">
			<Loader2
				className="h-9 w-9 text-muted-foreground animate-spin"
				strokeWidth={1.5}
				aria-hidden
			/>
			<p className={wpText.muted}>{label}</p>
		</div>
	)
}

const errorTitles: Record<WpErrorKind, string> = {
	permission: "无访问权限",
	not_found: "未找到内容",
	auth: "需要登录",
	invalid_link: "链接无效",
	network: "网络异常",
	unknown: "无法加载",
}

const errorHints: Record<WpErrorKind, string> = {
	permission:
		"当前账号可能没有该单据或功能的权限。请联系管理员分配权限，或换用有权限的账号。",
	not_found: "内容可能不存在、编号有误或已被删除。",
	auth: "登录状态已失效，请重新登录后再试。",
	invalid_link: "链接不完整、已过期或已被使用，请向相关人员索取新链接。",
	network: "请检查网络后重试；若使用企业 App，请确认可访问服务器。",
	unknown: "若问题持续，请联系管理员并说明本页提示。",
}

/** 列表无数据、功能占位等 */
export function WpEmptyState({
	icon: Icon = Inbox,
	title,
	description,
	className,
	children,
}: {
	icon?: LucideIcon
	title: string
	description?: string
	className?: string
	children?: React.ReactNode
}) {
	return (
		<Card className={className}>
			<CardContent className="flex flex-col items-center px-6 py-10 text-center space-y-4">
				<div className="rounded-full bg-muted p-3.5">
					<Icon className="h-8 w-8 text-muted-foreground" strokeWidth={1.5} />
				</div>
				<div className="space-y-1.5 max-w-sm">
					<p className="text-base font-semibold tracking-tight text-foreground">
						{title}
					</p>
					{description ? (
						<p className={wpText.muted}>{description}</p>
					) : null}
				</div>
				{children ? <div className="flex flex-col gap-2 w-full max-w-xs">{children}</div> : null}
			</CardContent>
		</Card>
	)
}

/** 请求失败 / 权限不足 / 单据不可见（带服务端 message） */
export function WpRequestFailed({
	message,
	kind: kindProp,
	title,
	hint,
	className,
	children,
}: {
	message: string
	kind?: WpErrorKind
	title?: string
	hint?: string
	className?: string
	children?: React.ReactNode
}) {
	const kind = kindProp ?? classifyWorkerPortalError(message)
	const IconMap: Record<WpErrorKind, LucideIcon> = {
		permission: ShieldAlert,
		not_found: SearchX,
		auth: KeyRound,
		invalid_link: Link2Off,
		network: WifiOff,
		unknown: AlertCircle,
	}
	const Icon = IconMap[kind]
	const warnKind = kind === "permission" || kind === "auth"
	const iconWrapClass = warnKind
		? "rounded-full bg-amber-500/10 p-3.5"
		: "rounded-full bg-destructive/10 p-3.5"
	const iconClass = warnKind
		? "h-8 w-8 text-amber-700 dark:text-amber-400"
		: "h-8 w-8 text-destructive"

	return (
		<Card className={className}>
			<CardContent className="px-6 py-8 space-y-4">
				<div className="flex flex-col items-center text-center space-y-3">
					<div className={iconWrapClass}>
						<Icon className={iconClass} strokeWidth={1.5} />
					</div>
					<div className="space-y-2 max-w-md w-full">
						<p className="text-base font-semibold tracking-tight">
							{title ?? errorTitles[kind]}
						</p>
						{message ? (
							<p
								className={`${wpText.body} rounded-md bg-muted/60 px-3 py-2 text-left break-words`}
							>
								{message}
							</p>
						) : null}
						<p className={wpText.muted}>{hint ?? errorHints[kind]}</p>
					</div>
				</div>
				{children ? <div className="flex flex-col gap-2 pt-1">{children}</div> : null}
			</CardContent>
		</Card>
	)
}

/** 操作成功收尾（审批提交等） */
export function WpSuccessState({
	title,
	description,
	children,
}: {
	title: string
	description?: string
	children?: React.ReactNode
}) {
	return (
		<Card>
			<CardContent className="flex flex-col items-center px-6 py-10 text-center space-y-4">
				<div className="rounded-full bg-primary/10 p-3.5">
					<CheckCircle2 className="h-8 w-8 text-primary" strokeWidth={1.5} />
				</div>
				<div className="space-y-1.5">
					<p className="text-base font-semibold tracking-tight">{title}</p>
					{description ? (
						<p className={wpText.muted}>{description}</p>
					) : null}
				</div>
				{children ? <div className="w-full max-w-xs">{children}</div> : null}
			</CardContent>
		</Card>
	)
}

/** 路由不存在等 */
export function WpNotFoundState({
	title = "页面不存在",
	description = "当前地址未对应 Worker Portal 中的功能，请从应用内入口重新打开。",
	children,
}: {
	title?: string
	description?: string
	children?: React.ReactNode
}) {
	return (
		<WpEmptyState icon={SearchX} title={title} description={description}>
			{children}
		</WpEmptyState>
	)
}
