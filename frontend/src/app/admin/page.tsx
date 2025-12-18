'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Users, Activity, AlertTriangle, CheckCircle } from "lucide-react"

export default function AdminPage() {
    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">System Overview</h1>
                    <p className="text-slate-400">Monitor system performance and user activity.</p>
                </div>
            </div>

            {/* Admin Stats */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-cyan-500/20 bg-cyan-500/5">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-cyan-400">Total Users</CardTitle>
                        <Users className="h-4 w-4 text-cyan-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">0</div>
                        <p className="text-xs text-slate-400">active accounts</p>
                    </CardContent>
                </Card>

                <Card className="border-emerald-500/20 bg-emerald-500/5">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-emerald-400">System Health</CardTitle>
                        <Activity className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">100%</div>
                        <p className="text-xs text-emerald-500 flex items-center gap-1">
                            <CheckCircle size={12} /> All systems operational
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-yellow-500/20 bg-yellow-500/5">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-yellow-400">API Latency</CardTitle>
                        <Activity className="h-4 w-4 text-yellow-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">124ms</div>
                        <p className="text-xs text-slate-400">average response time</p>
                    </CardContent>
                </Card>

                <Card className="border-red-500/20 bg-red-500/5">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-red-400">Error Rate</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">0.01%</div>
                        <p className="text-xs text-slate-400">last 24 hours</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Recent Registrations</CardTitle>
                        <CardDescription>New users who joined recently.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="text-sm text-slate-500 text-center py-6">No new users today.</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>System Logs</CardTitle>
                        <CardDescription>Latest system events and warnings.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="text-sm text-slate-500 text-center py-6">No critical logs found.</div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
