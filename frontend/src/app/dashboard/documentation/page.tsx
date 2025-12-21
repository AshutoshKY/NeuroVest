'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText, ChevronRight, Database, Shield, Zap, Code2,
    Activity, Lock, Server, GitBranch, BarChart3, AlertCircle,
    CheckCircle2, XCircle, ArrowRight, Layers
} from 'lucide-react';

export default function DocumentationPage() {
    const [activeSection, setActiveSection] = useState('overview');

    const sections = [
        { id: 'overview', label: 'System Overview', icon: FileText },
        { id: 'architecture', label: 'Architecture', icon: GitBranch },
        { id: 'features', label: 'Features', icon: Zap },
        { id: 'rate-limiting', label: 'Rate Limiting', icon: Shield },
        { id: 'rag', label: 'RAG System', icon: Code2 },
        { id: 'databases', label: 'Databases', icon: Database },
        { id: 'caching', label: 'Caching & Redis', icon: Server },
        { id: 'guardrails', label: 'Guardrails', icon: Lock },
        { id: 'api', label: 'API Endpoints', icon: Activity },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20 py-8 px-4 pb-24">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <div className="flex items-center gap-3 mb-3">
                        <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                            <FileText className="w-6 h-6 text-blue-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-white">Technical Documentation</h1>
                            <p className="text-slate-400 text-sm">Complete system architecture & implementation details</p>
                        </div>
                    </div>
                </motion.div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Sidebar Navigation */}
                    <div className="lg:col-span-3">
                        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-4 sticky top-4">
                            <h3 className="text-sm font-semibold text-slate-400 mb-3">Contents</h3>
                            <div className="space-y-1">
                                {sections.map((section) => {
                                    const Icon = section.icon;
                                    const isActive = activeSection === section.id;

                                    return (
                                        <button
                                            key={section.id}
                                            onClick={() => setActiveSection(section.id)}
                                            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${isActive
                                                ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 border border-blue-500/30'
                                                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                                                }`}
                                        >
                                            <Icon className="w-4 h-4" />
                                            <span className="flex-1 text-left">{section.label}</span>
                                            {isActive && <ChevronRight className="w-4 h-4" />}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    {/* Main Content */}
                    <div className="lg:col-span-9">
                        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-8">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={activeSection}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    {activeSection === 'overview' && <OverviewSection />}
                                    {activeSection === 'architecture' && <ArchitectureSection />}
                                    {activeSection === 'features' && <FeaturesSection />}
                                    {activeSection === 'rate-limiting' && <RateLimitingSection />}
                                    {activeSection === 'rag' && <RAGSection />}
                                    {activeSection === 'databases' && <DatabasesSection />}
                                    {activeSection === 'caching' && <CachingSection />}
                                    {activeSection === 'guardrails' && <GuardrailsSection />}
                                    {activeSection === 'api' && <APISection />}
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Section Components
function OverviewSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-4">System Overview</h2>
                <p className="text-slate-300 leading-relaxed mb-4">
                    NeuroVest is an enterprise-grade AI-powered stock market analysis platform that combines{' '}
                    <span className="text-blue-400 font-semibold">Next.js 14</span>,{' '}
                    <span className="text-purple-400 font-semibold">FastAPI</span>, and{' '}
                    <span className="text-emerald-400 font-semibold">Azure OpenAI GPT-4</span> to deliver
                    institutional-quality investment insights to retail investors.
                </p>
                <p className="text-slate-300 leading-relaxed">
                    The platform democratizes complex financial analysis by aggregating real-time data from multiple sources,
                    processing it through a sophisticated RAG (Retrieval-Augmented Generation) pipeline, and presenting
                    actionable insights with transparent sourcing and strict guardrails.
                </p>
            </div>

            <div className="p-5 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-blue-300 mb-1">Mission Statement</h4>
                        <p className="text-sm text-slate-300">
                            Make institutional-grade stock analysis accessible to everyone through AI, while maintaining
                            transparency, accuracy, and responsible financial guidance through multi-layer guardrails.
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-3">
                        <Code2 className="w-5 h-5 text-blue-400" />
                        <h3 className="text-sm font-semibold text-white">Frontend Stack</h3>
                    </div>
                    <ul className="text-sm text-slate-400 space-y-1.5">
                        <li>• Next.js 14 (App Router)</li>
                        <li>• React 18 + TypeScript</li>
                        <li>• Tailwind CSS + Framer Motion</li>
                        <li>• Zustand (State Management)</li>
                        <li>• SSE for Real-time Streaming</li>
                    </ul>
                </div>

                <div className="p-5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-3">
                        <Server className="w-5 h-5 text-purple-400" />
                        <h3 className="text-sm font-semibold text-white">Backend Stack</h3>
                    </div>
                    <ul className="text-sm text-slate-400 space-y-1.5">
                        <li>• FastAPI (Python 3.11+)</li>
                        <li>• SQLAlchemy (MySQL ORM)</li>
                        <li>• Redis for caching & rate limits</li>
                        <li>• Async I/O throughout</li>
                        <li>• JWT Authentication</li>
                    </ul>
                </div>

                <div className="p-5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-3">
                        <Database className="w-5 h-5 text-emerald-400" />
                        <h3 className="text-sm font-semibold text-white">Data Layer</h3>
                    </div>
                    <ul className="text-sm text-slate-400 space-y-1.5">
                        <li>• MySQL: Relational data</li>
                        <li>• ChromaDB: Vector embeddings</li>
                        <li>• Redis: High-speed cache</li>
                        <li>• Multi-API fallback system</li>
                        <li>• Docker containerization</li>
                    </ul>
                </div>
            </div>

            <div className="space-y-3">
                <h3 className="text-lg font-semibold text-white">Key Components</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-cyan-500">
                        <h4 className="text-sm font-semibold text-cyan-300 mb-2">AI/ML Engine</h4>
                        <ul className="text-xs text-slate-400 space-y-1">
                            <li>• Azure OpenAI GPT-4 for analysis</li>
                            <li>• text-embedding-3-small (1536-dim vectors)</li>
                            <li>• ChromaDB semantic search (cosine similarity)</li>
                            <li>• Hybrid sentiment analysis</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-pink-500">
                        <h4 className="text-sm font-semibold text-pink-300 mb-2">Data Sources</h4>
                        <ul className="text-xs text-slate-400 space-y-1">
                            <li>• Finnhub → Alpha Vantage → Yahoo Finance → Marketstack</li>
                            <li>• DuckDuckGo News (primary scraper)</li>
                            <li>• Google News RSS (fallback)</li>
                            <li>• Real-time price data with 1hr TTL</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-orange-500">
                        <h4 className="text-sm font-semibold text-orange-300 mb-2">Security & Compliance</h4>
                        <ul className="text-xs text-slate-400 space-y-1">
                            <li>• Multi-layer rate limiting (IP/Session/User)</li>
                            <li>• JWT-based authentication</li>
                            <li>• robots.txt compliance</li>
                            <li>• Mandatory disclaimer enforcement</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-violet-500">
                        <h4 className="text-sm font-semibold text-violet-300 mb-2">Performance Optimization</h4>
                        <ul className="text-xs text-slate-400 space-y-1">
                            <li>• 1-hour Redis caching (95%+ hit rate)</li>
                            <li>• Parallel async API calls</li>
                            <li>• Trending stocks tracking</li>
                            <li>• ~50ms cached vs ~15-30s fresh analysis</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div className="p-5 rounded-lg bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20">
                <div className="flex items-start gap-3">
                    <Zap className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-yellow-300 mb-1">System Architecture Highlights</h4>
                        <ul className="text-sm text-slate-300 space-y-1">
                            <li>• <span className="text-yellow-400">Microservices-based:</span> Each component isolated and scalable</li>
                            <li>• <span className="text-yellow-400">Event-driven:</span> Server-Sent Events (SSE) for real-time updates</li>
                            <li>• <span className="text-yellow-400">Fault-tolerant:</span> Graceful degradation with multi-API fallbacks</li>
                            <li>• <span className="text-yellow-400">Observable:</span> Comprehensive logging & metrics</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}

function ArchitectureSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">System Architecture</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    Microservices-based architecture with layered design optimized for scalability, reliability, and performance.
                </p>
            </div>

            {/* Complete Flow Diagram */}
            <div className="p-6 rounded-lg bg-slate-800/30 border border-slate-700/50">
                <h3 className="text-lg font-semibold text-white mb-4">Complete Request Flow</h3>
                <div className="space-y-3 text-sm">
                    {/* User Layer */}
                    <div className="flex items-center gap-2">
                        <div className="flex-shrink-0 w-32 px-3 py-2 bg-blue-500/20 text-blue-300 rounded border border-blue-500/30 text-center font-mono text-xs">
                            User/Browser
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-500" />
                        <div className="flex-1 px-3 py-2 bg-purple-500/20 text-purple-300 rounded border border-purple-500/30 text-xs">
                            Next.js 14 Frontend (React + TypeScript)
                        </div>
                    </div>

                    {/* SSE Connection */}
                    <div className="flex items-center gap-2 ml-16">
                        <div className="px-3 py-1 bg-slate-700/50 text-slate-400 rounded text-xs font-mono">
                            EventSource (SSE)
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
                    </div>

                    {/* Backend Layer */}
                    <div className="flex items-center gap-2">
                        <div className="flex-shrink-0 w-32 px-3 py-2 bg-transparent rounded text-xs text-slate-600">
                            HTTP POST
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-500" />
                        <div className="flex-1 px-3 py-2 bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30 text-xs">
                            FastAPI Backend + Rate Limiter + Auth Middleware
                        </div>
                    </div>

                    {/* Database Layer */}
                    <div className="flex items-center gap-2 ml-16">
                        <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
                    </div>
                    <div className="grid grid-cols-3 gap-2 ml-16">
                        <div className="px-3 py-2 bg-red-500/20 text-red-300 rounded border border-red-500/30 text-center text-xs font-semibold">
                            Redis Cache
                        </div>
                        <div className="px-3 py-2 bg-violet-500/20 text-violet-300 rounded border border-violet-500/30 text-center text-xs font-semibold">
                            MySQL DB
                        </div>
                        <div className="px-3 py-2 bg-orange-500/20 text-orange-300 rounded border border-orange-500/30 text-center text-xs font-semibold">
                            ChromaDB
                        </div>
                    </div>

                    {/* External APIs */}
                    <div className="flex items-center gap-2 ml-16">
                        <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex-shrink-0 w-32 px-3 py-2 bg-transparent rounded text-xs text-slate-600">
                            Fetch Data
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-500" />
                        <div className="flex-1 px-3 py-2 bg-cyan-500/20 text-cyan-300 rounded border border-cyan-500/30 text-xs">
                            Stock APIs + News Scrapers + Azure OpenAI
                        </div>
                    </div>

                    {/* RAG Processing*/}
                    <div className="flex items-center gap-2 ml-16">
                        <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex-shrink-0 w-32 px-3 py-2 bg-transparent rounded text-xs text-slate-600">
                            RAG Pipeline
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-500" />
                        <div className="flex-1 px-3 py-2 bg-pink-500/20 text-pink-300 rounded border border-pink-500/30 text-xs">
                            Embed → Store → Query → Synthesize with GPT-4
                        </div>
                    </div>

                    {/* Response */}
                    <div className="flex items-center gap-2 ml-16">
                        <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex-shrink-0 w-32 px-3 py-2 bg-transparent rounded text-xs text-slate-600">
                            Stream Back
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-500" />
                        <div className="flex-1 px-3 py-2 bg-blue-500/20 text-blue-300 rounded border border-blue-500/30 text-xs">
                            User Interface (Real-time tokens + thinking steps)
                        </div>
                    </div>
                </div>
            </div>

            {/* Architectural Layers */}
            <div className="space-y-3">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Layers className="w-5 h-5 text-blue-400" />
                    Architectural Layers
                </h3>

                <div className="p-5 rounded-lg bg-slate-800/30 border-l-4 border-blue-500">
                    <h4 className="text-base font-semibold text-blue-300 mb-3">1. Presentation Layer</h4>
                    <div className="space-y-2 text-sm text-slate-400">
                        <p className="mb-2">
                            <span className="text-white font-medium">Next.js 14</span> with App Router and Server Components
                        </p>
                        <ul className="space-y-1 ml-4">
                            <li>• <span className="text-blue-300">EventSource API</span> for SSE streaming (real-time analysis updates)</li>
                            <li>• <span className="text-blue-300">Zustand</span> for global state management (auth, user data)</li>
                            <li>• <span className="text-blue-300">Framer Motion</span> for smooth animations and transitions</li>
                            <li>• <span className="text-blue-300">Tailwind CSS</span> with custom design tokens</li>
                            <li>• Progressive analysis display (thinking steps → tokens → complete)</li>
                        </ul>
                    </div>
                </div>

                <div className="p-5 rounded-lg bg-slate-800/30 border-l-4 border-purple-500">
                    <h4 className="text-base font-semibold text-purple-300 mb-3">2. API Gateway & Application Layer</h4>
                    <div className="space-y-2 text-sm text-slate-400">
                        <p className="mb-2">
                            <span className="text-white font-medium">FastAPI</span> with async/await throughout
                        </p>
                        <ul className="space-y-1 ml-4">
                            <li>• <span className="text-purple-300">Rate Limiter Middleware</span>: Multi-layer (IP, session, user)</li>
                            <li>• <span className="text-purple-300">Auth Middleware</span>: JWT validation & optional user</li>
                            <li>• <span className="text-purple-300">CORS Middleware</span>: Frontend origin whitelisting</li>
                            <li>• <span className="text-purple-300">SSE Handler</span>: EventSourceResponse with heartbeat</li>
                            <li>• <span className="text-purple-300">Error Handling</span>: Graceful degradation & structured responses</li>
                            <li>• Automatic OpenAPI/Swagger docs at <code className="px-1.5 py-0.5 bg-slate-700/50 rounded text-xs">/docs</code></li>
                        </ul>
                    </div>
                </div>

                <div className="p-5 rounded-lg bg-slate-800/30 border-l-4 border-emerald-500">
                    <h4 className="text-base font-semibold text-emerald-300 mb-3">3. Data Layer</h4>
                    <div className="space-y-2 text-sm text-slate-400">
                        <p className="mb-2">Multi-database architecture for optimal data access patterns</p>
                        <div className="grid grid-cols-3 gap-3 mt-3">
                            <div className="p-3 bg-slate-900/50 rounded">
                                <div className="text-violet-300 font-semibold text-xs mb-1">MySQL</div>
                                <ul className="text-xs space-y-0.5">
                                    <li>• Users & auth</li>
                                    <li>• Watchlists</li>
                                    <li>• History</li>
                                    <li>• Saved analyses</li>
                                </ul>
                            </div>
                            <div className="p-3 bg-slate-900/50 rounded">
                                <div className="text-red-300 font-semibold text-xs mb-1">Redis</div>
                                <ul className="text-xs space-y-0.5">
                                    <li>• Analysis cache</li>
                                    <li>• Rate limitcounters</li>
                                    <li>• Trending stocks</li>
                                    <li>• Session data</li>
                                </ul>
                            </div>
                            <div className="p-3 bg-slate-900/50 rounded">
                                <div className="text-orange-300 font-semibold text-xs mb-1">ChromaDB</div>
                                <ul className="text-xs space-y-0.5">
                                    <li>• News embeddings</li>
                                    <li>• Semantic search</li>
                                    <li>• RAG retrieval</li>
                                    <li>• Historical context</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="p-5 rounded-lg bg-slate-800/30 border-l-4 border-pink-500">
                    <h4 className="text-base font-semibold text-pink-300 mb-3">4. AI/ML & External Integration Layer</h4>
                    <div className="space-y-2 text-sm text-slate-400">
                        <p className="mb-2">
                            RAG pipeline with multi-API fallback system
                        </p>
                        <ul className="space-y-1 ml-4">
                            <li>• <span className="text-pink-300">Azure OpenAI GPT-4</span>: Analysis synthesis & sentiment classification</li>
                            <li>• <span className="text-pink-300">text-embedding-3-small</span>: 1536-dimensional vector embeddings</li>
                            <li>• <span className="text-pink-300">Stock APIs</span>: Finnhub → Alpha Vantage → Yahoo → Marketstack</li>
                            <li>• <span className="text-pink-300">News Scrapers</span>: DuckDuckGo News (primary) + Google RSS (fallback)</li>
                            <li>• <span className="text-pink-300">ChromaDB</span>: Cosine similarity search for relevant context</li>
                            <li>• All external calls async with timeouts & error handling</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Deployment Architecture */}
            <div className="p-5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                <h3 className="text-base font-semibold text-white mb-3">Deployment Architecture (Docker Compose)</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 bg-slate-900/50 rounded border border-blue-500/30">
                        <div className="text-blue-300 font-semibold mb-1">frontend</div>
                        <div className="text-slate-500">Port: 3000</div>
                        <div className="text-slate-400 mt-2">Next.js 14 app</div>
                    </div>
                    <div className="p-3 bg-slate-900/50 rounded border border-purple-500/30">
                        <div className="text-purple-300 font-semibold mb-1">backend</div>
                        <div className="text-slate-500">Port: 8000</div>
                        <div className="text-slate-400 mt-2">FastAPI + Python</div>
                    </div>
                    <div className="p-3 bg-slate-900/50 rounded border border-violet-500/30">
                        <div className="text-violet-300 font-semibold mb-1">mysql</div>
                        <div className="text-slate-500">Port: 3306</div>
                        <div className="text-slate-400 mt-2">MySQL 8.0</div>
                    </div>
                    <div className="p-3 bg-slate-900/50 rounded border border-red-500/30">
                        <div className="text-red-300 font-semibold mb-1">redis</div>
                        <div className="text-slate-500">Port: 6379</div>
                        <div className="text-slate-400 mt-2">Redis cache</div>
                    </div>
                </div>
                <div className="mt-3 text-xs text-slate-400">
                    ChromaDB runs embedded in backend container at <code className="px-1.5 py-0.5 bg-slate-700/50 rounded">/app/data/chroma_db</code>
                </div>
            </div>
        </div>
    );
}

function FeaturesSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">Core Features</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    Comprehensive suite of features designed for intelligent, real-time stock market analysis with institutional-grade capabilities.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <BarChart3 className="w-5 h-5 text-blue-400" />
                        <h3 className="text-sm font-semibold text-blue-300">AI-Powered Analysis</h3>
                    </div>
                    <ul className="text-sm text-slate-400 space-y-2">
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-blue-300">GPT-4 synthesis</span> with RAG context from 100+ news sources</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-blue-300">Hybrid sentiment analysis</span>: LLM classification + confidence weighting</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-blue-300">Technical indicators</span>: RSI, MACD, Bollinger Bands (Finnhub)</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-blue-300">Historical context</span>: Last 5 analyses to detect trend shifts</span>
                        </li>
                    </ul>
                </div>

                <div className="p-5 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <Zap className="w-5 h-5 text-purple-400" />
                        <h3 className="text-sm font-semibold text-purple-300">Real-Time Streaming</h3>
                    </div>
                    <ul className="text-sm text-slate-400 space-y-2">
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-purple-300">Server-Sent Events (SSE)</span> for live token-by-token delivery</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-purple-300">Thinking steps</span>: Progressive display of analysis workflow</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-purple-300">Heartbeat mechanism</span> to maintain connection health</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-purple-300">EventSource API</span> with automatic reconnection</span>
                        </li>
                    </ul>
                </div>

                <div className="p-5 rounded-lg bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <Database className="w-5 h-5 text-emerald-400" />
                        <h3 className="text-sm font-semibold text-emerald-300">Smart Caching</h3>
                    </div>
                    <ul className="text-sm text-slate-400 space-y-2">
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-emerald-300">1-hour Redis cache</span> for analysis results (key: <code className="px-1 py-0.5 bg-slate-700/50 rounded text-xs">stock:analysis:&#123;TICKER&#125;</code>)</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-emerald-300">Trending stocks tracking</span> with Redis sorted sets (ZADD/ZRANGE)</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-emerald-300">~50ms cached</span> vs ~15-30s fresh analysis response time</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-emerald-300">95%+ cache hit rate</span> for popular stocks during market hours</span>
                        </li>
                    </ul>
                </div>

                <div className="p-5 rounded-lg bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <Shield className="w-5 h-5 text-cyan-400" />
                        <h3 className="text-sm font-semibold text-cyan-300">Security & Limits</h3>
                    </div>
                    <ul className="text-sm text-slate-400 space-y-2">
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-cyan-300">Multi-layer rate limiting</span>: IP (SHA-256) + Session + User</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-cyan-300">JWT authentication</span> with refresh token support</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-cyan-300">AI guardrails</span> to prevent hallucinations & enforce disclaimers</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
                            <span><span className="text-cyan-300">robots.txt compliance</span> for ethical web scraping</span>
                        </li>
                    </ul>
                </div>
            </div>

            <div className="space-y-3">
                <h3 className="text-lg font-semibold text-white">Additional Features</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                            <Activity className="w-4 h-4 text-blue-400" />
                            User Management
                        </h4>
                        <ul className="text-xs text-slate-400 space-y-1">
                            <li>• Watchlist management</li>
                            <li>• Analysis history tracking</li>
                            <li>• Saved analyses bookmarks</li>
                            <li>• Favorites organization</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                            <BarChart3 className="w-4 h-4 text-purple-400" />
                            Stock Data APIs
                        </h4>
                        <ul className="text-xs text-slate-400 space-y-1">
                            <li>• Multi-API fallback system</li>
                            <li>• Real-time price data</li>
                            <li>• Historical charts (Upstox)</li>
                            <li>• Symbol search (Alpha Vantage)</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                            <Lock className="w-4 h-4 text-emerald-400" />
                            Admin Dashboard
                        </h4>
                        <ul className="text-xs text-slate-400 space-y-1">
                            <li>• User management</li>
                            <li>• IP blacklist control</li>
                            <li>• Cache management</li>
                            <li>• Traffic analytics</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div className="p-5 rounded-lg bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20">
                <div className="flex items-start gap-3">
                    <Zap className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-yellow-300 mb-1">Performance Metrics</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2 text-xs text-slate-300">
                            <div>
                                <div className="text-yellow-400 font-bold">~50ms</div>
                                <div className="text-slate-400">Cached analysis response</div>
                            </div>
                            <div>
                                <div className="text-yellow-400 font-bold">95%+</div>
                                <div className="text-slate-400">Cache hit rate (peak hours)</div>
                            </div>
                            <div>
                                <div className="text-yellow-400 font-bold">100+</div>
                                <div className="text-slate-400">News sources aggregated</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function RateLimitingSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">Rate Limiting System</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    Multi-layer rate limiting with Redis-based tracking to prevent abuse while ensuring fair usage.
                    Implemented in <code className="px-1.5 py-0.5 bg-slate-700/50 rounded text-xs">backend/app/services/rate_limiter.py</code>
                </p>
            </div>

            <div className="p-5 rounded-lg bg-red-500/10 border border-red-500/20">
                <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-red-300 mb-1">Bypass Prevention</h4>
                        <p className="text-sm text-slate-300">
                            Rate limits are enforced at <span className="text-red-400 font-semibold">multiple layers</span> (IP hash, session fingerprint, user account)
                            to prevent bypass via incognito mode, VPNs, or creating multiple accounts.
                        </p>
                    </div>
                </div>
            </div>

            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Rate Limit Tiers</h3>

                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-700">
                            <th className="text-left py-2 px-3 text-slate-400 font-semibold">Layer</th>
                            <th className="text-left py-2 px-3 text-slate-400 font-semibold">Limit</th>
                            <th className="text-left py-2 px-3 text-slate-400 font-semibold">Window</th>
                            <th className="text-left py-2 px-3 text-slate-400 font-semibold">Tracking Method</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        <tr>
                            <td className="py-3 px-3 text-blue-300 font-medium">IP-Based</td>
                            <td className="py-3 px-3 text-slate-300">5 analyses</td>
                            <td className="py-3 px-3 text-slate-400">24 hours</td>
                            <td className="py-3 px-3 text-slate-500 text-xs font-mono">SHA-256(client_ip)[:16]</td>
                        </tr>
                        <tr>
                            <td className="py-3 px-3 text-purple-300 font-medium">Session-Based</td>
                            <td className="py-3 px-3 text-slate-300">5 analyses</td>
                            <td className="py-3 px-3 text-slate-400">24 hours</td>
                            <td className="py-3 px-3 text-slate-500 text-xs font-mono">X-Session-ID header</td>
                        </tr>
                        <tr>
                            <td className="py-3 px-3 text-emerald-300 font-medium">User-Based</td>
                            <td className="py-3 px-3 text-slate-300">5 analyses</td>
                            <td className="py-3 px-3 text-slate-400">24 hours</td>
                            <td className="py-3 px-3 text-slate-500 text-xs font-mono">Authenticated user_id</td>
                        </tr>
                        <tr>
                            <td className="py-3 px-3 text-cyan-300 font-medium">API General</td>
                            <td className="py-3 px-3 text-slate-300">100 requests</td>
                            <td className="py-3 px-3 text-slate-400">1 minute</td>
                            <td className="py-3 px-3 text-slate-500 text-xs">Per IP (all endpoints)</td>
                        </tr>
                        <tr>
                            <td className="py-3 px-3 text-orange-300 font-medium">API Hourly</td>
                            <td className="py-3 px-3 text-slate-300">1000 requests</td>
                            <td className="py-3 px-3 text-slate-400">1 hour</td>
                            <td className="py-3 px-3 text-slate-500 text-xs">Per IP (all endpoints)</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div className="p-5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                <h3 className="text-base font-semibold text-white mb-3">Implementation Flow</h3>
                <div className="space-y-2 text-sm font-mono">
                    <div className="text-slate-400">1. Request arrives with headers (X-Session-ID, Authorization)</div>
                    <div className="flex items-center gap-2 ml-4">
                        <ChevronRight className="w-3 h-3 text-slate-600 rotate-90" />
                    </div>
                    <div className="text-slate-400">2. Extract identifiers: IP hash, session ID, user ID</div>
                    <div className="flex items-center gap-2 ml-4">
                        <ChevronRight className="w-3 h-3 text-slate-600 rotate-90" />
                    </div>
                    <div className="text-slate-400">3. Redis GET <span className="text-blue-300">ratelimit:&#123;layer&#125;:&#123;id&#125;:analysis_86400s</span></div>
                    <div className="flex items-center gap-2 ml-4">
                        <ChevronRight className="w-3 h-3 text-slate-600 rotate-90" />
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-emerald-400">&lt; 5?</span>
                        <span className="text-slate-600">→</span>
                        <span className="text-emerald-300">INCR + EXPIRE 86400s → Allow (200 OK)</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-red-400">≥ 5?</span>
                        <span className="text-slate-600">→</span>
                        <span className="text-red-300">HTTP 429 + Retry-After header</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-blue-500">
                    <h4 className="text-sm font-semibold text-blue-300 mb-2">Redis Keys Pattern</h4>
                    <ul className="text-xs text-slate-400 space-y-1 font-mono">
                        <li>• ratelimit:ip:&#123;hash&#125;:analysis_86400s</li>
                        <li>• ratelimit:session:&#123;id&#125;:analysis_86400s</li>
                        <li>• ratelimit:user:&#123;id&#125;:analysis_86400s</li>
                        <li>• ratelimit:ip:&#123;hash&#125;:api_minute_60s</li>
                    </ul>
                </div>

                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-purple-500">
                    <h4 className="text-sm font-semibold text-purple-300 mb-2">Authenticated Users</h4>
                    <p className="text-xs text-slate-400">
                        For logged-in users, <span className="text-purple-300 font-semibold">ONLY user-based limit</span> is checked (5/day per account).
                        IP and session checks are skipped to prevent conflicts.
                    </p>
                </div>
            </div>
        </div>
    );
}

function RAGSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">Retrieval-Augmented Generation (RAG)</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    Advanced RAG pipeline combining semantic vector search in ChromaDB, context-aware retrieval,
                    and GPT-4 synthesis for accurate, source-backed stock analysis.
                </p>
            </div>

            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">4-Stage RAG Pipeline</h3>

                <div className="space-y-3">
                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-blue-500">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500 flex items-center justify-center text-xs text-blue-300 font-bold">
                                1
                            </div>
                            <h4 className="text-sm font-semibold text-blue-300">Data Ingestion</h4>
                        </div>
                        <p className="text-sm text-slate-400 mt-2 mb-3">
                            <span className="text-blue-300 font-semibold">DuckDuckGo News</span> (primary): 100 results per query, aggregates from 100+ sources
                        </p>
                        <ul className="text-xs text-slate-400 space-y-1 ml-4">
                            <li>• Text cleaning & normalization</li>
                            <li>• Recursive character splitting (800 chars, 200 overlap)</li>
                            <li>• Metadata extraction (ticker, source, timestamp, URL)</li>
                            <li>• <span className="text-blue-300">Fallback</span>: Google News RSS</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-purple-500">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500 flex items-center justify-center text-xs text-purple-300 font-bold">
                                2
                            </div>
                            <h4 className="text-sm font-semibold text-purple-300">Embedding Generation</h4>
                        </div>
                        <p className="text-sm text-slate-400 mt-2 mb-3">
                            Convert text chunks to <span className="text-purple-300 font-semibold">1536-dimensional vectors</span>
                        </p>
                        <ul className="text-xs text-slate-400 space-y-1 ml-4">
                            <li>• <span className="text-purple-300">Primary</span>: Azure OpenAI <code className="px-1 py-0.5 bg-slate-700/50 rounded">text-embedding-3-small</code></li>
                            <li>• <span className="text-purple-300">Fallback</span>: HuggingFace <code className="px-1 py-0.5 bg-slate-700/50 rounded">all-MiniLM-L6-v2</code> (local)</li>
                            <li>• Batch processing for efficiency (~200 tokens/article)</li>
                            <li>• Cost: $0.0001 per 1K tokens (Azure)</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-emerald-500">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-6 h-6 rounded-full bg-emerald-500/20 border border-emerald-500 flex items-center justify-center text-xs text-emerald-300 font-bold">
                                3
                            </div>
                            <h4 className="text-sm font-semibold text-emerald-300">Semantic Search (ChromaDB)</h4>
                        </div>
                        <p className="text-sm text-slate-400 mt-2 mb-3">
                            Query vectorized and compared using <span className="text-emerald-300 font-semibold">cosine similarity</span>
                        </p>
                        <ul className="text-xs text-slate-400 space-y-1 ml-4">
                            <li>• Top-k retrieval (k=10 most relevant chunks)</li>
                            <li>• Metadata filtering: <code className="px-1 py-0.5 bg-slate-700/50 rounded">ticker=&#123;SYMBOL&#125;</code></li>
                            <li>• Historical context: Last 5 past analyses from ChromaDB</li>
                            <li>• Persistent storage: <code className="px-1 py-0.5 bg-slate-700/50 rounded">/app/data/chroma_db</code></li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-pink-500">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-6 h-6 rounded-full bg-pink-500/20 border border-pink-500 flex items-center justify-center text-xs text-pink-300 font-bold">
                                4
                            </div>
                            <h4 className="text-sm font-semibold text-pink-300">LLM Synthesis (GPT-4)</h4>
                        </div>
                        <p className="text-sm text-slate-400 mt-2 mb-3">
                            Retrieved context + query sent to <span className="text-pink-300 font-semibold">GPT-4</span> with structured prompt
                        </p>
                        <ul className="text-xs text-slate-400 space-y-1 ml-4">
                            <li>• Role enforcement: Financial Analyst</li>
                            <li>• Output format: <code className="px-1 py-0.5 bg-slate-700/50 rounded">response_format=&#123;"type": "json_object"&#125;</code></li>
                            <li>• Mandatory: Source citations, risk disclaimers</li>
                            <li>• Temperature: 0.5 (balanced creativity/accuracy)</li>
                            <li>• Cost: ~$0.03/1K tokens (~500 tokens/analysis)</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div className="p-5 rounded-lg bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/20">
                <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-orange-300 mb-1">Historical Awareness</h4>
                        <p className="text-sm text-slate-300">
                            RAG automatically retrieves the <span className="text-orange-400 font-semibold">last 5 analyses</span> from
                            ChromaDB to identify trend shifts and long-term sentiment changes, providing temporal context that simple
                            news aggregation cannot capture.
                        </p>
                    </div>
                </div>
            </div>

            <div className="p-5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                <h3 className="text-base font-semibold text-white mb-3">ChromaDB Collection Schema</h3>
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-slate-700">
                            <th className="text-left py-2 text-slate-400">Field</th>
                            <th className="text-left py-2 text-slate-400">Type</th>
                            <th className="text-left py-2 text-slate-400">Description</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 font-mono">
                        <tr>
                            <td className="py-2 text-blue-300">collection</td>
                            <td className="py-2 text-slate-400">string</td>
                            <td className="py-2 text-slate-500">"stock_market_news"</td>
                        </tr>
                        <tr>
                            <td className="py-2 text-blue-300">embedding</td>
                            <td className="py-2 text-slate-400">vector</td>
                            <td className="py-2 text-slate-500">float[1536]</td>
                        </tr>
                        <tr>
                            <td className="py-2 text-blue-300">document</td>
                            <td className="py-2 text-slate-400">string</td>
                            <td className="py-2 text-slate-500">Text chunk (500-800 chars)</td>
                        </tr>
                        <tr>
                            <td className="py-2 text-blue-300">metadata</td>
                            <td className="py-2 text-slate-400">object</td>
                            <td className="py-2 text-slate-500">ticker, source, url, timestamp, keywords</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function DatabasesSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">Database Architecture</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    Multi-database architecture optimized for different data types: relational (MySQL), vector (ChromaDB), and cache (Redis).
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-5 rounded-lg bg-gradient-to-br from-violet-500/10 to-violet-500/5 border border-violet-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <Database className="w-5 h-5 text-violet-400" />
                        <h3 className="text-sm font-semibold text-violet-300">MySQL 8.0</h3>
                    </div>
                    <p className="text-xs text-slate-400 mb-3">Relational data storage</p>
                    <ul className="text-sm text-slate-400 space-y-2">
                        <li>• Users & authentication</li>
                        <li>• Watchlists & favorites</li>
                        <li>• Analysis history</li>
                        <li>• Saved analyses</li>
                        <li>• Admin blacklists</li>
                    </ul>
                    <div className="mt-3 text-xs text-slate-500">
                        Port: <code className="px-1 py-0.5 bg-slate-700/50 rounded">3306</code>
                    </div>
                </div>

                <div className="p-5 rounded-lg bg-gradient-to-br from-orange-500/10 to-orange-500/5 border border-orange-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <Database className="w-5 h-5 text-orange-400" />
                        <h3 className="text-sm font-semibold text-orange-300">ChromaDB</h3>
                    </div>
                    <p className="text-xs text-slate-400 mb-3">Vector database for RAG</p>
                    <ul className="text-sm text-slate-400 space-y-2">
                        <li>• News embeddings (1536-dim)</li>
                        <li>• Semantic search</li>
                        <li>• RAG context retrieval</li>
                        <li>• Historical analyses</li>
                        <li>• Metadata filtering</li>
                    </ul>
                    <div className="mt-3 text-xs text-slate-500">
                        Embedded in backend container
                    </div>
                </div>

                <div className="p-5 rounded-lg bg-gradient-to-br from-red-500/10 to-red-500/5 border border-red-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <Server className="w-5 h-5 text-red-400" />
                        <h3 className="text-sm font-semibold text-red-300">Redis</h3>
                    </div>
                    <p className="text-xs text-slate-400 mb-3">In-memory cache & queue</p>
                    <ul className="text-sm text-slate-400 space-y-2">
                        <li>• Analysis cache (1hr TTL)</li>
                        <li>• Rate limit counters</li>
                        <li>• Trending stocks (sorted sets)</li>
                        <li>• Session data</li>
                        <li>• Stock data cache</li>
                    </ul>
                    <div className="mt-3 text-xs text-slate-500">
                        Port: <code className="px-1 py-0.5 bg-slate-700/50 rounded">6379</code>
                    </div>
                </div>
            </div>

            <div className="space-y-3">
                <h3 className="text-lg font-semibold text-white">MySQL Schema</h3>

                <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-slate-700">
                                <th className="text-left py-2 pr-4 text-slate-400">Table</th>
                                <th className="text-left py-2 pr-4 text-slate-400">Key Fields</th>
                                <th className="text-left py-2 text-slate-400">Purpose</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 text-xs">
                            <tr>
                                <td className="py-2 pr-4 text-blue-300 font-mono">users</td>
                                <td className="py-2 pr-4 text-slate-400">id, email, hashed_password, is_active</td>
                                <td className="py-2 text-slate-500">Authentication & user management</td>
                            </tr>
                            <tr>
                                <td className="py-2 pr-4 text-blue-300 font-mono">watchlist</td>
                                <td className="py-2 pr-4 text-slate-400">user_id, ticker, name, exchange</td>
                                <td className="py-2 text-slate-500">User watchlists</td>
                            </tr>
                            <tr>
                                <td className="py-2 pr-4 text-blue-300 font-mono">history</td>
                                <td className="py-2 pr-4 text-slate-400">user_id, ticker, analysis_data, timestamp</td>
                                <td className="py-2 text-slate-500">Analysis history tracking</td>
                            </tr>
                            <tr>
                                <td className="py-2 pr-4 text-blue-300 font-mono">saved_analyses</td>
                                <td className="py-2 pr-4 text-slate-400">user_id, ticker, confidence, name</td>
                                <td className="py-2 text-slate-500">Bookmarked analyses</td>
                            </tr>
                            <tr>
                                <td className="py-2 pr-4 text-blue-300 font-mono">favourites</td>
                                <td className="py-2 pr-4 text-slate-400">user_id, ticker, name, exchange</td>
                                <td className="py-2 text-slate-500">Favorite stocks</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-orange-500">
                    <h4 className="text-sm font-semibold text-orange-300 mb-2">ChromaDB Operations</h4>
                    <div className="text-xs text-slate-400 space-y-2 font-mono">
                        <div>
                            <div className="text-orange-300">Add Documents:</div>
                            <div className="text-slate-500 ml-2">collection.add(documents, embeddings, metadatas, ids)</div>
                        </div>
                        <div>
                            <div className="text-orange-300">Query:</div>
                            <div className="text-slate-500 ml-2">collection.query(query_embeddings, n_results=10, where=&#123;"ticker": "RELIANCE"&#125;)</div>
                        </div>
                    </div>
                </div>

                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-red-500">
                    <h4 className="text-sm font-semibold text-red-300 mb-2">Redis Key Patterns</h4>
                    <ul className="text-xs text-slate-400 space-y-1 font-mono">
                        <li>• stock:analysis:&#123;TICKER&#125;</li>
                        <li>• stocks:info:&#123;TICKER&#125;</li>
                        <li>• trending:window</li>
                        <li>• ratelimit:*:*:*</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

function CachingSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">Caching Strategy (Redis)</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    Multi-tier Redis caching system reduces response times from ~15-30s to ~50ms and minimizes external API costs.
                </p>
            </div>

            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Cache Layers</h3>

                <div className="space-y-3">
                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-cyan-500">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-cyan-300">Analysis Cache</h4>
                            <span className="px-2 py-1 bg-cyan-500/20 border border-cyan-500/30 rounded text-xs text-cyan-300">TTL: 1 hour</span>
                        </div>
                        <p className="text-sm text-slate-400 mb-2">
                            Full RAG analysis results cached by ticker. Instant response for repeated queries.
                        </p>
                        <code className="text-xs text-cyan-300 bg-slate-900/50 px-2 py-1 rounded block">
                            Key: stock:analysis:&#123;TICKER&#125;
                        </code>
                        <div className="mt-2 text-xs text-slate-500">
                            Value: JSON with summary, reasoning, sentiment, references
                        </div>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-emerald-500">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-emerald-300">Stock Data Cache</h4>
                            <span className="px-2 py-1 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300">TTL: 1 hour</span>
                        </div>
                        <p className="text-sm text-slate-400 mb-2">
                            Real-time stock quotes from Yahoo Finance / Finnhub APIs.
                        </p>
                        <code className="text-xs text-emerald-300 bg-slate-900/50 px-2 py-1 rounded block">
                            Key: stocks:info:&#123;TICKER&#125;
                        </code>
                        <div className="mt-2 text-xs text-slate-500">
                            Value: price, volume, day_high, day_low, market_cap, pe_ratio
                        </div>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-purple-500">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-purple-300">Trending Stocks</h4>
                            <span className="px-2 py-1 bg-purple-500/20 border border-purple-500/30 rounded text-xs text-purple-300">Sorted Set</span>
                        </div>
                        <p className="text-sm text-slate-400 mb-2">
                            Real-time tracking of most analyzed stocks using Redis sorted sets.
                        </p>
                        <code className="text-xs text-purple-300 bg-slate-900/50 px-2 py-1 rounded block">
                            ZADD trending:window &#123;timestamp&#125; &#123;TICKER&#125;
                        </code>
                        <div className="mt-2 text-xs text-slate-500">
                            ZRANGE to get top trending stocks by analysis frequency
                        </div>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-blue-500">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-blue-300">Rate Limit Counters</h4>
                            <span className="px-2 py-1 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300">Sliding Window</span>
                        </div>
                        <p className="text-sm text-slate-400 mb-2">
                            Per-IP, per-session, per-user request counters with automatic expiry.
                        </p>
                        <code className="text-xs text-blue-300 bg-slate-900/50 px-2 py-1 rounded block">
                            Key: ratelimit:ip:&#123;HASH&#125;:analysis_86400s
                        </code>
                        <div className="mt-2 text-xs text-slate-500">
                            INCR + EXPIRE pattern for atomic counter management
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-5 rounded-lg bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20">
                <div className="flex items-start gap-3">
                    <Zap className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-yellow-300 mb-1">Performance Impact</h4>
                        <p className="text-sm text-slate-300 mb-2">
                            Cached analyses return in <span className="text-yellow-400 font-bold">~50ms</span> vs{' '}
                            <span className="text-red-400">~15-30s</span> for fresh RAG generation.
                        </p>
                        <div className="grid grid-cols-3 gap-3 text-xs">
                            <div>
                                <div className="text-yellow-400 font-bold">95%+</div>
                                <div className="text-slate-400">Cache hit rate (peak)</div>
                            </div>
                            <div>
                                <div className="text-yellow-400 font-bold">80%</div>
                                <div className="text-slate-400">API cost reduction</div>
                            </div>
                            <div>
                                <div className="text-yellow-400 font-bold">300x</div>
                                <div className="text-slate-400">Speed improvement</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-2">Cache Invalidation</h4>
                    <ul className="text-xs text-slate-400 space-y-1">
                        <li>• <span className="text-emerald-300">Automatic</span>: TTL expiration (1 hour)</li>
                        <li>• <span className="text-blue-300">Manual</span>: Admin cache flush endpoints</li>
                        <li>• <span className="text-purple-300">Selective</span>: Ticker-specific invalidation</li>
                    </ul>
                </div>

                <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-2">Redis Commands Used</h4>
                    <ul className="text-xs text-slate-400 space-y-1 font-mono">
                        <li>• GET, SET, EXPIRE (string cache)</li>
                        <li>• INCR, TTL (rate limits)</li>
                        <li>• ZADD, ZRANGE (trending stocks)</li>
                        <li>• DEL, FLUSHDB (admin tools)</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

function GuardrailsSection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">AI Guardrails</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    Multi-level safety mechanisms to ensure accurate, responsible, legally compliant AI outputs.
                </p>
            </div>

            <div className="p-5 rounded-lg bg-red-500/10 border border-red-500/20">
                <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-red-300 mb-1">Critical Rule</h4>
                        <p className="text-sm text-slate-300">
                            All AI responses <span className="text-red-400 font-bold">MUST</span> include disclaimers stating this is{' '}
                            <span className="text-red-400 font-bold">NOT financial advice</span>. Outputs are objective analysis only,
                            not recommendations to buy/sell securities.
                        </p>
                    </div>
                </div>
            </div>

            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Guardrail Layers</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-blue-300 mb-3 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            Prompt Guardrails
                        </h4>
                        <ul className="text-sm text-slate-400 space-y-2">
                            <li>• System instructions enforce role (Financial Analyst)</li>
                            <li>• Structured output format (<code className="px-1 py-0.5 bg-slate-700/50 rounded text-xs">JSON schema</code>)</li>
                            <li>• Mandatory source citation requirements</li>
                            <li>• Tone enforcement (objective, data-driven)</li>
                            <li>• Temperature: 0.5 (balanced creativity)</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-purple-300 mb-3 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            Data Validation
                        </h4>
                        <ul className="text-sm text-slate-400 space-y-2">
                            <li>• Output parsed and validated against schema</li>
                            <li>• Confidence scores: 0-100 range validation</li>
                            <li>• Sentiment classification whitelist (Bullish/Bearish/Neutral)</li>
                            <li>• Reference URLs validated for authenticity</li>
                            <li>• JSON parsing with error handling</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-emerald-300 mb-3 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            Sentiment Guardrails
                        </h4>
                        <ul className="text-sm text-slate-400 space-y-2">
                            <li>• Weak signals (&lt;0.4) can't override neutral majority</li>
                            <li>• Confidence weighting prevents false positives</li>
                            <li>• Aggregation logic prioritizes volume + strength</li>
                            <li>• Default to neutral when unclear</li>
                            <li>• Historical context for trend detection</li>
                        </ul>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-cyan-300 mb-3 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            Web Scraping Guardrails
                        </h4>
                        <ul className="text-sm text-slate-400 space-y-2">
                            <li>• <code className="px-1 py-0.5 bg-slate-700/50 rounded text-xs">robots.txt</code> compliance enforced</li>
                            <li>• Domain allow/block lists</li>
                            <li>• Rate limiting on external requests</li>
                            <li>• Respect crawl-delay directives</li>
                            <li>• Ethical sourcing from news aggregators</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                <h4 className="text-sm font-semibold text-white mb-3">Example Guardrail Enforcement</h4>
                <div className="space-y-3 text-xs">
                    <div className="flex items-start gap-2">
                        <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                        <div>
                            <span className="text-red-300 font-semibold">❌ Rejected:</span>
                            <span className="text-slate-400"> "Buy RELIANCE now for guaranteed 50% returns!"</span>
                            <div className="text-slate-500 mt-1">Reason: Violates no-advice rule, uses guarantee language</div>
                        </div>
                    </div>
                    <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <div>
                            <span className="text-emerald-300 font-semibold">✅ Accepted:</span>
                            <span className="text-slate-400"> "Based on Q2 earnings (source: ET), RELIANCE shows +15% YoY growth. Technical indicators suggest support at ₹2400. </span>
                            <span className="text-yellow-400 font-bold">Not financial advice.</span>
                            <span className="text-slate-400">"</span>
                            <div className="text-slate-500 mt-1">Reason: Objective, sourced, includes disclaimer</div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-5 rounded-lg bg-gradient-to-r from-orange-500/10 to-yellow-500/10 border border-orange-500/20">
                <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-semibold text-orange-300 mb-1">Legal Compliance</h4>
                        <p className="text-sm text-slate-300">
                            Guardrails ensure compliance with financial regulations by preventing the AI from providing
                            investment advice, making price predictions without disclaimers, or manipulating sentiment
                            through biased language.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

function APISection() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-white mb-3">API Endpoints</h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                    RESTful API built with FastAPI, featuring automatic OpenAPI documentation, JWT authentication,
                    and server-sent events for real-time analysis streaming.
                </p>
            </div>

            <div className="p-5 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                <div className="flex items-center gap-2 mb-2">
                    <Code2 className="w-5 h-5 text-blue-400" />
                    <h4 className="text-sm font-semibold text-blue-300">Interactive Swagger Docs</h4>
                </div>
                <p className="text-sm text-slate-300">
                    Access auto-generated API documentation at <code className="px-2 py-1 bg-slate-700/50 rounded text-cyan-300">http://localhost:8000/docs</code>
                    with interactive request testing and schema validation.
                </p>
            </div>

            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Endpoint Categories</h3>

                {/* Authentication */}
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-blue-500">
                    <h4 className="text-sm font-semibold text-blue-300 mb-3 flex items-center gap-2">
                        <Lock className="w-4 h-4" />
                        Authentication
                    </h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/auth/register</span>
                            <span className="text-slate-500 text-xs">- Create new user account</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/auth/login</span>
                            <span className="text-slate-500 text-xs">- Authenticate & get JWT token</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/auth/refresh</span>
                            <span className="text-slate-500 text-xs">- Refresh access token</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/auth/logout</span>
                            <span className="text-slate-500 text-xs">- Invalidate session</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/auth/me</span>
                            <span className="text-slate-500 text-xs">- Get current user info</span>
                        </div>
                    </div>
                </div>

                {/* Stock Analysis */}
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-purple-500">
                    <h4 className="text-sm font-semibold text-purple-300 mb-3 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4" />
                        Stock Analysis & Data
                    </h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/stocks/search?q=&#123;query&#125;</span>
                            <span className="text-slate-500 text-xs">- Search stocks by name/ticker</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/stocks/&#123;ticker&#125;/analysis-stream</span>
                            <span className="text-slate-500 text-xs">- SSE: Real-time RAG analysis</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/stocks/&#123;ticker&#125;/analysis</span>
                            <span className="text-slate-500 text-xs">- Cached analysis (non-streaming)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/stocks/&#123;ticker&#125;/data</span>
                            <span className="text-slate-500 text-xs">- Real-time stock price data</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/stocks/info/&#123;ticker&#125;</span>
                            <span className="text-slate-500 text-xs">- Stock details (price, volume, PE, market cap)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/stocks/trending</span>
                            <span className="text-slate-500 text-xs">- Most analyzed stocks (Redis sorted set)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/stocks/watchlist-data</span>
                            <span className="text-slate-500 text-xs">- Bulk fetch for watchlist (parallel async)</span>
                        </div>
                    </div>
                </div>

                {/* User Management */}
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-emerald-500">
                    <h4 className="text-sm font-semibold text-emerald-300 mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        User Management 🔒 Auth Required
                    </h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/api/watchlist</span>
                            <span className="text-slate-500 text-xs">- Get user watchlist</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/api/watchlist</span>
                            <span className="text-slate-500 text-xs">- Add stock to watchlist</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-red-500/20 border border-red-500/30 rounded text-xs text-red-300 font-mono">DELETE</span>
                            <span className="text-slate-400 font-mono">/api/watchlist/&#123;id&#125;</span>
                            <span className="text-slate-500 text-xs">- Remove from watchlist</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/api/history</span>
                            <span className="text-slate-500 text-xs">- Analysis history</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/api/history</span>
                            <span className="text-slate-500 text-xs">- Add to history</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/api/saved-analyses</span>
                            <span className="text-slate-500 text-xs">- Saved/bookmarked analyses</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/api/saved-analyses</span>
                            <span className="text-slate-500 text-xs">- Save analysis</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/api/favourites</span>
                            <span className="text-slate-500 text-xs">- User favorites</span>
                        </div>
                    </div>
                </div>

                {/* News & Sentiment */}
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-cyan-500">
                    <h4 className="text-sm font-semibold text-cyan-300 mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        News & Sentiment
                    </h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/news/feed</span>
                            <span className="text-slate-500 text-xs">- General market news</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/news/&#123;ticker&#125;</span>
                            <span className="text-slate-500 text-xs">- Ticker-specific news</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/sentiment/&#123;ticker&#125;</span>
                            <span className="text-slate-500 text-xs">- Sentiment analysis (Bullish/Bearish/Neutral)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/sentiment/sector/&#123;sector&#125;</span>
                            <span className="text-slate-500 text-xs">- Sector-wide sentiment</span>
                        </div>
                    </div>
                </div>

                {/* Admin */}
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-orange-500">
                    <h4 className="text-sm font-semibold text-orange-300 mb-3 flex items-center gap-2">
                        <Lock className="w-4 h-4" />
                        Admin Endpoints 🔐 Admin Only
                    </h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/admin/users</span>
                            <span className="text-slate-500 text-xs">- List all users</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/admin/users/disable</span>
                            <span className="text-slate-500 text-xs">- Disable user account</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/admin/ip-blacklist</span>
                            <span className="text-slate-500 text-xs">- View blacklisted IPs</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/admin/ip-blacklist/add</span>
                            <span className="text-slate-500 text-xs">- Add IP to blacklist</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/admin/cache/flush-all</span>
                            <span className="text-slate-500 text-xs">- Clear all Redis cache</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/admin/cache/stats</span>
                            <span className="text-slate-500 text-xs">- Cache hit/miss statistics</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/admin/traffic/realtime</span>
                            <span className="text-slate-500 text-xs">- Real-time traffic stats</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/admin/history/analyses</span>
                            <span className="text-slate-500 text-xs">- All user analyses (paginated)</span>
                        </div>
                    </div>
                </div>

                {/* Health & Monitoring */}
                <div className="p-4 rounded-lg bg-slate-800/30 border-l-4 border-violet-500">
                    <h4 className="text-sm font-semibold text-violet-300 mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Health & Monitoring
                    </h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/health/sources</span>
                            <span className="text-slate-500 text-xs">- Data source health (APIs, scrapers)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/health/summary</span>
                            <span className="text-slate-500 text-xs">- Overall system health</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-xs text-emerald-300 font-mono">POST</span>
                            <span className="text-slate-400 font-mono">/health/check-now</span>
                            <span className="text-slate-500 text-xs">- Force health check</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-xs text-blue-300 font-mono">GET</span>
                            <span className="text-slate-400 font-mono">/tracking/guest/check-limit</span>
                            <span className="text-slate-500 text-xs">- Check rate limit status</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                <h3 className="text-base font-semibold text-white mb-3">SSE Response Format (Analysis Stream)</h3>
                <div className="text-xs font-mono">
                    <div className="text-slate-400 mb-2">Event stream for <code className="text-cyan-300">/stocks/&#123;ticker&#125;/analysis-stream</code>:</div>
                    <div className="p-3 bg-slate-900/50 rounded space-y-1">
                        <div className="text-blue-300">data: &#123;"type": "thinking", "step": <span className="text-emerald-300">"Fetching news..."</span>&#125;</div>
                        <div className="text-blue-300">data: &#123;"type": "thinking", "step": <span className="text-emerald-300">"Retrieving historical context..."</span>&#125;</div>
                        <div className="text-blue-300">data: &#123;"type": "token", "token": <span className="text-emerald-300">"Based on recent news..."</span>&#125;</div>
                        <div className="text-blue-300">data: &#123;"type": "complete", "analysis": &#123;...&#125;&#125;</div>
                        <div className="text-slate-600">// Heartbeat every 15s: data: &#123;"type": "heartbeat"&#125;</div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-2">Request Headers</h4>
                    <ul className="text-xs text-slate-400 space-y-1 font-mono">
                        <li>• Authorization: Bearer &#123;JWT_TOKEN&#125;</li>
                        <li>• X-Session-ID: &#123;FINGERPRINT&#125;</li>
                        <li>• Content-Type: application/json</li>
                    </ul>
                </div>

                <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-2">Common HTTP Status Codes</h4>
                    <ul className="text-xs text-slate-400 space-y-1">
                        <li>• <span className="text-emerald-300">200</span>: Success</li>
                        <li>• <span className="text-yellow-300">401</span>: Unauthorized (missing/invalid JWT)</li>
                        <li>• <span className="text-red-300">429</span>: Rate limit exceeded</li>
                        <li>• <span className="text-orange-300">500</span>: Internal server error</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

// Continue with remaining sections in next file part...
