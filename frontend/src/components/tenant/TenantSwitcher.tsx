"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Check, ChevronsUpDown, PlusCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    SelectSeparator,
} from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import {
    type Tenant,
    getMyTenants,
    createTenant,
    switchTenant,
    getActiveTenantId
} from "@/lib/tenant";

export function TenantSwitcher() {
    const router = useRouter();
    const { toast } = useToast();
    const [open, setOpen] = React.useState(false);
    const [showNewTenantDialog, setShowNewTenantDialog] = React.useState(false);
    const [tenants, setTenants] = React.useState<Tenant[]>([]);
    const [activeTenant, setActiveTenant] = React.useState<Tenant | null>(null);
    const [newTenantName, setNewTenantName] = React.useState("");
    const [isLoading, setIsLoading] = React.useState(false);

    // Fetch tenants on mount
    React.useEffect(() => {
        const fetchTenants = async () => {
            const data = await getMyTenants();
            setTenants(data);

            const activeId = getActiveTenantId();
            if (activeId) {
                const found = data.find((t) => t.id === activeId);
                if (found) setActiveTenant(found);
            } else if (data.length > 0) {
                // Fallback to first tenant if none active
                setActiveTenant(data[0]);
                // Also simpler to just set it active
                // switchTenant(data[0].id); 
            }
        };
        fetchTenants();
    }, []);

    const handleTenantChange = async (value: string) => {
        if (value === "create-new") {
            setShowNewTenantDialog(true);
            return;
        }

        const selected = tenants.find((t) => t.id === value);
        if (selected) {
            const success = await switchTenant(selected.id);
            if (success) {
                setActiveTenant(selected);
                toast({
                    title: "Tenant switched",
                    description: `You are now working in ${selected.name}`,
                });
                router.refresh();
                // Optional: reload page to ensure data freshness
                // window.location.reload(); 
            }
        }
    };

    const handleCreateTenant = async () => {
        if (!newTenantName.trim()) return;

        setIsLoading(true);
        try {
            const newTenant = await createTenant(newTenantName);
            toast({
                title: "Tenant created",
                description: `${newTenantName} has been created successfully.`,
            });

            // Refresh list
            const updatedTenants = await getMyTenants();
            setTenants(updatedTenants);

            // Switch to new tenant
            const created = updatedTenants.find(t => t.slug === newTenant.slug || t.name === newTenantName);
            if (created) {
                await switchTenant(created.id);
                setActiveTenant(created);
                router.refresh();
            }

            setShowNewTenantDialog(false);
            setNewTenantName("");
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to create tenant. Please try again.",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={showNewTenantDialog} onOpenChange={setShowNewTenantDialog}>
            <Select
                onValueChange={handleTenantChange}
                value={activeTenant?.id}
            >
                <SelectTrigger className="w-[200px] border-white/10 bg-white/5 text-white hover:bg-white/10">
                    <SelectValue placeholder="Select tenant...">
                        {activeTenant ? (
                            <span className="font-medium">{activeTenant.name}</span>
                        ) : (
                            "Select tenant..."
                        )}
                    </SelectValue>
                </SelectTrigger>
                <SelectContent>
                    {tenants.map((tenant) => (
                        <SelectItem key={tenant.id} value={tenant.id}>
                            {tenant.name}
                        </SelectItem>
                    ))}
                    <SelectSeparator />
                    <SelectItem value="create-new" className="text-blue-500 font-medium">
                        <div className="flex items-center gap-2">
                            <PlusCircle className="h-4 w-4" />
                            Create Tenant
                        </div>
                    </SelectItem>
                </SelectContent>
            </Select>

            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Create Valid Tenant</DialogTitle>
                    <DialogDescription>
                        Add a new organization to your account.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="name" className="text-right">
                            Name
                        </Label>
                        <Input
                            id="name"
                            value={newTenantName}
                            onChange={(e) => setNewTenantName(e.target.value)}
                            className="col-span-3"
                            placeholder="Acme Corp"
                            autoFocus
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => setShowNewTenantDialog(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleCreateTenant} disabled={isLoading}>
                        {isLoading ? "Creating..." : "Create Tenant"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
