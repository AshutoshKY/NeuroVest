'use client';

/**
 * Kill Switches & Controls Page
 * 
 * Matches POC: admin_controls.html
 * - Emergency Shutdown button
 * - Granular toggle controls
 * - Force logout action
 * 
 * SUPER_ADMIN required for all actions
 * Only reason required for confirmation (no typed codes)
 */

import { useState } from 'react';
import { useKillSwitches, useSessionControl } from '@/hooks/useAdminAPI';
import { AlertTriangle } from 'lucide-react';

export default function ControlsPage() {
    const { switches, activateSwitch, deactivateSwitch, isLoading } = useKillSwitches();
    const { forceLogoutAll, status } = useSessionControl();

    const [confirmModal, setConfirmModal] = useState<{
        type: string;
        action: 'activate' | 'deactivate' | 'logout';
        title: string;
        description: string;
    } | null>(null);
    const [actionReason, setActionReason] = useState('');
    const [securityPin, setSecurityPin] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAction = async () => {
        if (!confirmModal) return;

        if (!actionReason.trim()) {
            setError('Please provide a reason for this action');
            return;
        }

        if (!securityPin.trim()) {
            setError('Security PIN is required');
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            if (confirmModal.action === 'activate') {
                await activateSwitch(confirmModal.type, confirmModal.type.toUpperCase(), actionReason, securityPin);
            } else if (confirmModal.action === 'deactivate') {
                await deactivateSwitch(confirmModal.type, actionReason, securityPin);
            } else if (confirmModal.action === 'logout') {
                await forceLogoutAll('LOGOUT_ALL', actionReason);
            }
            setConfirmModal(null);
            setActionReason('');
            setSecurityPin('');
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : 'Action failed';
            setError(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };

    const toggleSwitch = (switchType: string, currentActive: boolean, description: string) => {
        setConfirmModal({
            type: switchType,
            action: currentActive ? 'deactivate' : 'activate',
            title: currentActive ? `Deactivate ${switchType.replace(/_/g, ' ')}?` : `Activate ${switchType.replace(/_/g, ' ')}?`,
            description
        });
    };

    return (
        <>
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-red-500/5 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-red-400 flex items-center gap-2">
                    <AlertTriangle className="w-6 h-6" />
                    Critical Platform Controls
                </h1>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-12">

                {/* EMERGENCY SHUTDOWN */}
                <section className="bg-[#0f172a] border border-red-500 rounded-xl p-8 relative overflow-hidden shadow-2xl shadow-red-900/10">
                    <div className="absolute top-0 left-0 w-2 h-full bg-red-500"></div>
                    <div className="flex flex-col md:flex-row justify-between items-center gap-8">
                        <div>
                            <h2 className="text-2xl font-bold text-white">Emergency Shutdown</h2>
                            <p className="text-slate-400 mt-2 max-w-xl">
                                This will block all non-admin API traffic immediately. Admin access will be preserved.
                            </p>
                            {switches['emergency_shutdown']?.is_active && (
                                <div className="mt-4 text-red-400 text-sm font-bold animate-pulse">
                                    ⚠️ EMERGENCY SHUTDOWN IS CURRENTLY ACTIVE
                                </div>
                            )}
                        </div>
                        <button
                            onClick={() => {
                                const isActive = switches['emergency_shutdown']?.is_active;
                                setConfirmModal({
                                    type: 'emergency_shutdown',
                                    action: isActive ? 'deactivate' : 'activate',
                                    title: isActive ? 'Deactivate Emergency Shutdown?' : 'Activate Emergency Shutdown?',
                                    description: 'This will block all non-admin API traffic immediately.'
                                });
                            }}
                            disabled={isLoading}
                            className={`text-white text-lg font-bold py-4 px-10 rounded-lg shadow-lg transform active:scale-95 transition ${switches['emergency_shutdown']?.is_active
                                ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-900/40'
                                : 'bg-red-500 hover:bg-red-600 shadow-red-900/40'
                                }`}
                        >
                            {switches['emergency_shutdown']?.is_active ? 'DEACTIVATE KILL SWITCH' : 'ACTIVATE KILL SWITCH'}
                        </button>
                    </div>
                </section>

                {/* GRANULAR CONTROLS */}
                <section>
                    <h3 className="text-lg font-bold text-white mb-6">Granular Blocker Controls</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                        {/* Block Signups */}
                        <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl flex items-center justify-between">
                            <div>
                                <div className="font-bold text-white">Block Signups</div>
                                <div className="text-xs text-slate-500">Prevent new registrations</div>
                            </div>
                            <button
                                onClick={() => toggleSwitch('block_signups', switches['block_signups']?.is_active, 'Prevent new user registrations')}
                                className={`relative w-12 h-6 rounded-full transition-colors border-2 ${switches['block_signups']?.is_active ? 'bg-red-500 border-red-400' : 'bg-slate-700 border-slate-600'
                                    }`}
                            >
                                <span className={`absolute w-5 h-5 bg-white rounded-full top-0.5 left-0.5 transition-transform shadow-md ${switches['block_signups']?.is_active ? 'translate-x-6' : 'translate-x-0'
                                    }`}></span>
                            </button>
                        </div>

                        {/* Block Logins */}
                        <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl flex items-center justify-between">
                            <div>
                                <div className="font-bold text-white">Block Logins</div>
                                <div className="text-xs text-slate-500">Prevent session creation</div>
                            </div>
                            <button
                                onClick={() => toggleSwitch('block_logins', switches['block_logins']?.is_active, 'Prevent all login attempts')}
                                className={`relative w-12 h-6 rounded-full transition-colors border-2 ${switches['block_logins']?.is_active ? 'bg-red-500 border-red-400' : 'bg-slate-700 border-slate-600'
                                    }`}
                            >
                                <span className={`absolute w-5 h-5 bg-white rounded-full top-0.5 left-0.5 transition-transform shadow-md ${switches['block_logins']?.is_active ? 'translate-x-6' : 'translate-x-0'
                                    }`}></span>
                            </button>
                        </div>

                        {/* Flush All Sessions */}
                        <div className="bg-[#0f172a] border border-red-500/30 p-6 rounded-xl flex items-center justify-between">
                            <div>
                                <div className="font-bold text-red-400">Flush All Sessions</div>
                                <div className="text-xs text-slate-500">Force logout everyone</div>
                                <div className="text-xs text-slate-600 mt-1">Epoch: {status?.auth_epoch}</div>
                            </div>
                            <button
                                onClick={() => setConfirmModal({
                                    type: 'logout',
                                    action: 'logout',
                                    title: 'Force Logout All Users?',
                                    description: 'This will invalidate all active sessions and force all users to re-login.'
                                })}
                                className="bg-[#0f172a] border border-red-500 text-red-400 px-4 py-2 rounded font-bold text-xs hover:bg-red-500 hover:text-white transition"
                            >
                                EXECUTE
                            </button>
                        </div>

                        {/* Maintenance Mode */}
                        <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl flex items-center justify-between">
                            <div>
                                <div className="font-bold text-white">Maintenance Mode</div>
                                <div className="text-xs text-slate-500">Show maintenance page</div>
                            </div>
                            <button
                                onClick={() => toggleSwitch('maintenance_mode', switches['maintenance_mode']?.is_active, 'Show maintenance page to non-admin users')}
                                className={`relative w-12 h-6 rounded-full transition-colors border-2 ${switches['maintenance_mode']?.is_active ? 'bg-red-500 border-red-400' : 'bg-slate-700 border-slate-600'
                                    }`}
                            >
                                <span className={`absolute w-5 h-5 bg-white rounded-full top-0.5 left-0.5 transition-transform shadow-md ${switches['maintenance_mode']?.is_active ? 'translate-x-6' : 'translate-x-0'
                                    }`}></span>
                            </button>
                        </div>

                        {/* ReadOnly DB */}
                        <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl flex items-center justify-between">
                            <div>
                                <div className="font-bold text-white">ReadOnly DB</div>
                                <div className="text-xs text-slate-500">Block all writes</div>
                            </div>
                            <button
                                onClick={() => toggleSwitch('readonly_db', switches['readonly_db']?.is_active, 'Block all database write operations')}
                                className={`relative w-12 h-6 rounded-full transition-colors border-2 ${switches['readonly_db']?.is_active ? 'bg-red-500 border-red-400' : 'bg-slate-700 border-slate-600'
                                    }`}
                            >
                                <span className={`absolute w-5 h-5 bg-white rounded-full top-0.5 left-0.5 transition-transform shadow-md ${switches['readonly_db']?.is_active ? 'translate-x-6' : 'translate-x-0'
                                    }`}></span>
                            </button>
                        </div>

                    </div>
                </section>

            </div>

            {/* Confirmation Modal - Only requires reason now */}
            {confirmModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
                    <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl p-6 w-full max-w-md">
                        <h3 className="text-lg font-bold text-white mb-2">{confirmModal.title}</h3>

                        <p className="text-slate-400 text-sm mb-4">
                            {confirmModal.description}
                        </p>

                        <label className="block text-sm text-slate-400 mb-2">
                            Reason for this action <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={actionReason}
                            onChange={(e) => setActionReason(e.target.value)}
                            placeholder="e.g., Security incident, Scheduled maintenance..."
                            className="w-full bg-[#020617] border border-[#1e293b] rounded px-3 py-2 text-white mb-4"
                            autoFocus
                        />

                        <label className="block text-xs text-slate-400 mb-1">
                            Security PIN <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="password"
                            value={securityPin}
                            onChange={(e) => setSecurityPin(e.target.value)}
                            placeholder="Enter 6-digit security PIN"
                            maxLength={6}
                            className="w-full bg-[#020617] border border-amber-500/30 rounded px-3 py-2 text-white mb-4 font-mono tracking-widest text-center"
                        />

                        {error && (
                            <div className="text-red-400 text-sm mb-4">{error}</div>
                        )}

                        <div className="flex gap-4">
                            <button
                                onClick={() => {
                                    setConfirmModal(null);
                                    setActionReason('');
                                    setSecurityPin('');
                                    setError(null);
                                }}
                                className="flex-1 bg-[#1e293b] text-slate-400 py-2 rounded font-bold hover:bg-[#334155] transition"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAction}
                                disabled={isSubmitting || !actionReason.trim() || !securityPin.trim()}
                                className="flex-1 bg-red-500 text-white py-2 rounded font-bold hover:bg-red-600 transition disabled:opacity-50"
                            >
                                {isSubmitting ? 'Processing...' : 'Confirm'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

