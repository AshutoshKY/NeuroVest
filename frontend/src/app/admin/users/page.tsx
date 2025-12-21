'use client';

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Search, MoreVertical, Shield } from "lucide-react"

// Mock User Data
const users = [
    { id: 1, name: 'Alice Smith', email: 'alice@example.com', role: 'admin', status: 'verified', joined: '2023-10-01' },
    { id: 2, name: 'Bob Johnson', email: 'bob@example.com', role: 'user', status: 'verified', joined: '2023-10-05' },
    { id: 3, name: 'Charlie Brown', email: 'charlie@example.com', role: 'user', status: 'pending', joined: '2023-10-12' },
    { id: 4, name: 'David Lee', email: 'david@example.com', role: 'user', status: 'verified', joined: '2023-10-15' },
]

export default function UsersPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">User Management</h1>
                    <p className="text-slate-400">View and manage platform users.</p>
                </div>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>All Users</CardTitle>
                        <div className="relative">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
                            <input
                                type="text"
                                placeholder="Search users..."
                                className="h-9 w-[250px] rounded-md border border-slate-700 bg-slate-900 pl-9 pr-4 text-sm text-white focus:border-cyan-500 focus:outline-none"
                            />
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow className="border-slate-800 hover:bg-slate-900/50">
                                <TableHead className="text-slate-400">Name</TableHead>
                                <TableHead className="text-slate-400">Email</TableHead>
                                <TableHead className="text-slate-400">Role</TableHead>
                                <TableHead className="text-slate-400">Status</TableHead>
                                <TableHead className="text-slate-400">Joined</TableHead>
                                <TableHead className="text-right text-slate-400">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {users.map((user) => (
                                <TableRow key={user.id} className="border-slate-800 hover:bg-slate-900/50">
                                    <TableCell className="font-medium text-white">{user.name}</TableCell>
                                    <TableCell className="text-slate-300">{user.email}</TableCell>
                                    <TableCell>
                                        <Badge variant={user.role === 'admin' ? 'cyan' : 'default'} className="uppercase text-[10px]">
                                            {user.role}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={user.status === 'verified' ? 'emerald' : 'secondary'} className="capitalize">
                                            {user.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-slate-400">{user.joined}</TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="ghost" size="icon" className="h-8 w-8">
                                            <MoreVertical className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
