'use client';

import type { Scenario } from '@/lib/api/mappers';

/**
 * Scenario Grid - Pro Mode
 * Displays 3 scenarios (bull/base/bear) with probabilities
 * Matches design from analysis_8.html
 */

interface ScenarioGridProps {
    scenarios: Scenario[];
}

export function ScenarioGrid({ scenarios }: ScenarioGridProps) {
    if (!scenarios || scenarios.length === 0) {
        return (
            <div className="pro-element">
                <div className="p-8 text-center text-gray-500 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl">
                    No scenarios available
                </div>
            </div>
        );
    }

    // Sort scenarios: bull, base, bear
    const sortedScenarios = [...scenarios].sort((a, b) => {
        const order = { bull: 0, base: 1, bear: 2 };
        return (order[a.type] || 99) - (order[b.type] || 99);
    });

    // Find primary scenario (highest probability)
    const primaryScenario = scenarios.reduce((max, s) =>
        s.probability > max.probability ? s : max,
        scenarios[0]
    );

    const getScenarioColor = (type: string) => {
        if (type === 'bull') return {
            bg: 'bg-success/5',
            border: 'border-success/20',
            text: 'text-success',
            icon: '🚀'
        };
        if (type === 'bear') return {
            bg: 'bg-danger/5',
            border: 'border-danger/20',
            text: 'text-danger',
            icon: '⚠️'
        };
        return {
            bg: 'bg-primary-500/5',
            border: 'border-primary-500/20',
            text: 'text-primary-500',
            icon: '⚖️'
        };
    };

    return (
        <div className="pro-element space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Probabilistic Scenarios</h3>
                <span className="text-xs text-gray-500 font-mono">3 PATHS</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {sortedScenarios.slice(0, 3).map((scenario) => {
                    const colors = getScenarioColor(scenario.type);
                    const isPrimary = scenario.id === primaryScenario.id;

                    return (
                        <div
                            key={scenario.id}
                            className={`p-5 rounded-xl border transition-all ${isPrimary
                                    ? 'scenario-primary ring-2 ring-success/20'
                                    : 'bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800'
                                }`}
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl">{colors.icon}</span>
                                    <div>
                                        <div className={`text-sm font-bold ${colors.text} uppercase`}>
                                            {scenario.type} Case
                                        </div>
                                        {isPrimary && (
                                            <div className="text-xs text-success font-mono mt-0.5">
                                                PRIMARY
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Probability */}
                            <div className="mb-4">
                                <div className="flex items-end justify-between mb-2">
                                    <span className="text-xs text-gray-500 font-mono uppercase">Probability</span>
                                    <span className={`text-2xl font-bold ${colors.text} font-mono`}>
                                        {(scenario.probability * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                                    <div
                                        className={`${colors.bg.replace('/5', '')} h-full transition-all duration-500`}
                                        style={{ width: `${scenario.probability * 100}%` }}
                                    />
                                </div>
                            </div>

                            {/* Description */}
                            <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
                                {scenario.description || 'No description available'}
                            </p>

                            {/* Triggers */}
                            {scenario.trigger_conditions && (
                                <div className="mb-3 p-3 rounded-lg bg-gray-50 dark:bg-zinc-950 border border-gray-200 dark:border-zinc-800">
                                    <div className="text-xs text-gray-500 font-mono uppercase mb-1.5">Triggers</div>
                                    <div className="text-xs text-gray-700 dark:text-gray-300">
                                        {scenario.trigger_conditions}
                                    </div>
                                </div>
                            )}

                            {/* Invalidation */}
                            {scenario.invalidation_level && (
                                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30">
                                    <div className="text-xs text-red-600 dark:text-red-400 font-mono uppercase mb-1.5">
                                        Invalidation
                                    </div>
                                    <div className="text-xs text-red-700 dark:text-red-300 font-mono font-bold">
                                        {scenario.invalidation_level}
                                    </div>
                                </div>
                            )}

                            {/* Target Zone */}
                            {scenario.target_zone && (
                                <div className="mt-3 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30">
                                    <div className="text-xs text-emerald-600 dark:text-emerald-400 font-mono uppercase mb-1.5">
                                        Target Zone
                                    </div>
                                    <div className="text-xs text-emerald-700 dark:text-emerald-300 font-mono font-bold">
                                        {scenario.target_zone}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Footer Note */}
            <div className="text-xs text-gray-500 text-center font-mono">
                Probabilities sum to 100% | Based on deterministic signal engine
            </div>
        </div>
    );
}
