
import { redirect } from "next/navigation";

export default function LeadsPage() {
    // Default to import for now, or a list if it exists in future
    redirect("/leads/import");
}
