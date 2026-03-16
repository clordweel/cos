import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft } from "lucide-react"

export function Stock() {
	return (
		<div className="min-h-screen bg-muted/30">
			<header className="border-b bg-background px-4 py-3">
				<Link
					to="/worker-portal"
					className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
				>
					<ArrowLeft className="h-4 w-4 mr-2" />
					返回工作台
				</Link>
			</header>
			<main className="container max-w-2xl py-8 px-4">
				<Card>
					<CardHeader>
						<CardTitle>入库盘点</CardTitle>
						<CardDescription>入库盘点功能开发中。</CardDescription>
					</CardHeader>
					<CardContent>
						<Link to="/worker-portal">
							<Button variant="outline">
								<ArrowLeft className="h-4 w-4 mr-2" />
								返回工作台
							</Button>
						</Link>
					</CardContent>
				</Card>
			</main>
		</div>
	)
}
