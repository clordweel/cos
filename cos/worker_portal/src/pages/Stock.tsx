import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { WpEmptyState } from "@/components/wp-states"
import { Construction } from "lucide-react"
import { WpPage } from "@/lib/wp-layout"

export function Stock() {
	return (
		<WpPage>
			<WpEmptyState
				icon={Construction}
				title="功能筹备中"
				description="入库盘点将在后续版本开放，请从待报销审批等已上线功能进入。"
			>
				<Button variant="default" asChild className="w-full">
					<Link to="/worker-portal/pi-reimbursement-pending">前往待报销审批</Link>
				</Button>
			</WpEmptyState>
		</WpPage>
	)
}
