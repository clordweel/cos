import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft } from "lucide-react"
import { WpPage } from "@/lib/wp-layout"

export function Stock() {
	return (
		<WpPage>
			<Card>
				<CardHeader>
					<CardTitle>入库盘点</CardTitle>
					<CardDescription>功能开发中</CardDescription>
				</CardHeader>
				<CardContent>
					<Button variant="outline" asChild>
						<Link to="/worker-portal/pi-reimbursement-pending">
							<ArrowLeft className="h-4 w-4 mr-2" />
							返回待报销审批
						</Link>
					</Button>
				</CardContent>
			</Card>
		</WpPage>
	)
}
