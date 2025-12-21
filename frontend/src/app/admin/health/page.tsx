'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react"

// Mock Health Data
const services = [
    { name: 'MySQL Database', status: 'operational', latency: '45ms' },
    { name: 'Redis Cache', status: 'operational', latency: '12ms' },
    { name: 'ChromaDB Vector Store', status: 'operational', latency: '230ms' },
    { name: 'Authentication Service', status: 'operational', latency: '55ms' },
    { name: 'Market Data API (Finnhub)', status: 'operational', latency: '120ms' },
    { name: 'Market Data API (Alpha Vantage)', status: 'degraded', latency: '850ms' },
]

export default function HealthPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">System Health</h1>
                    <p className="text-slate-400">Real-time status of all system components and APIs.</p>
                </div>
            </div>

            <div className="grid gap-6">
                {services.map((service, index) => (
                    <Card key={index} className="flex flex-row items-center justify-between p-6">
                        <div className="flex items-center gap-4">
                            {service.status === 'operational' ? (
                                <CheckCircle className="h-8 w-8 text-emerald-500" />
                            ) : service.status === 'degraded' ? (
                                <AlertTriangle className="h-8 w-8 text-yellow-500" />
                            ) : (
                                <XCircle className="h-8 w-8 text-red-500" />
                            )}
                            <div>
                                <h3 className="text-lg font-medium text-white">{service.name}</h3>
                                <p className="text-sm text-slate-400">Latency: {service.latency}</p>
                            </div>
                        </div>
                        <Badge variant={
                            service.status === 'operational' ? 'emerald' :
                                service.status === 'degraded' ? 'secondary' : 'destructive'
                        } className="text-sm px-3 py-1 capitalize">
                            {service.status}
                        </Badge>
                    </Card>
                ))}
            </div>
        </div>
    );
}
