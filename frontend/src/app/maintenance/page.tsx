'use client';

/**
 * Maintenance Page
 * Shown to non-admin users when maintenance mode is active
 */

import { motion } from 'framer-motion';
import { Settings, Clock, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function MaintenancePage() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20 flex items-center justify-center p-6">
            {/* Animated background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <motion.div
                    className="absolute top-1/4 -left-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl"
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.3, 0.5, 0.3],
                    }}
                    transition={{ duration: 8, repeat: Infinity }}
                />
                <motion.div
                    className="absolute bottom-1/4 -right-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl"
                    animate={{
                        scale: [1.2, 1, 1.2],
                        opacity: [0.5, 0.3, 0.5],
                    }}
                    transition={{ duration: 8, repeat: Infinity, delay: 1 }}
                />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="relative z-10 text-center max-w-lg"
            >
                {/* Icon */}
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: "spring" }}
                    className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30 mb-8"
                >
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                    >
                        <Settings className="w-12 h-12 text-amber-400" />
                    </motion.div>
                </motion.div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                    Under Maintenance
                </h1>

                {/* Subtitle */}
                <p className="text-xl text-slate-400 mb-8">
                    We're making some improvements to serve you better.
                </p>

                {/* Status Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="bg-slate-900/50 backdrop-blur-xl border border-amber-500/20 rounded-2xl p-6 mb-8"
                >
                    <div className="flex items-center justify-center gap-3 text-amber-400">
                        <Clock className="w-5 h-5" />
                        <span className="font-medium">Scheduled Maintenance in Progress</span>
                    </div>
                    <p className="text-slate-500 mt-3 text-sm">
                        Our team is working to bring the platform back online as soon as possible.
                        Please check back shortly.
                    </p>
                </motion.div>

                {/* Features during maintenance */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
                        <div className="text-2xl mb-2">🔒</div>
                        <div className="text-xs text-slate-400">Data Safe</div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
                        <div className="text-2xl mb-2">⚡</div>
                        <div className="text-xs text-slate-400">Quick Return</div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
                        <div className="text-2xl mb-2">✨</div>
                        <div className="text-xs text-slate-400">Improvements</div>
                    </div>
                </div>

                {/* Back Link */}
                <Link
                    href="/"
                    className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-300 text-sm transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Home
                </Link>
            </motion.div>
        </div>
    );
}
