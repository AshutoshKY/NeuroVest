'use client';

import type { Scenario } from '@/lib/api/mappers';

/**
 * Scenario Summary - Lite Mode
 * Shows simplified single-card view of primary scenario
 * Matches design from analysis_8.html
 */

interface ScenarioSummaryProps {
    scenarios: Scenario[];
}

export function ScenarioSummary({ scenarios }: ScenarioSummaryProps) {
    if (!scenarios || scenarios.length === 0) {
        return (
            <div className="lite-element">
                <div className="p-6 text-center text-gray-500 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl">
                    No forecast available
                </div>
            </div>
        );
    }

    // Get primary scenario (highest probability)
    const primaryScenario = scenarios.reduce((max, s) =>
        s.probability > max.probability ? s : max,
        scenarios[0]
    );

    const getSimplifiedTitle = (type: string) => {
        if (type === 'bull') return 'Likely to Rise 📈';
        if (type === 'bear') return 'Likely to Fall 📉';
        return 'Likely to Stay Flat ➡️';
    };

    const getSimplifiedMessage = (scenario: Scenario) => {
        const confidence = (scenario.probability * 100).toFixed(0);

        if (scenario.type === 'bull') {
            return `Our AI predicts a ${confidence}% chance the stock will move upward. ${scenario.target_zone
                    ? `Expected to reach ${scenario.target_zone}.`
                    : ''
                }`;
        }

        if (scenario.type === 'bear') {
            return `Our AI predicts a ${confidence}% chance of downward movement. ${scenario.invalidation_level
                    ? `Watch for support at ${scenario.invalidation_level}.`
                    : ''
                }`;
        }

        return `Our AI predicts a ${confidence}% chance the stock will remain in a trading range.`;
    };

    const getBgGradient = (type: string) => {
        if (type === 'bull') return 'from-emerald-500/10 via-green-500/5 to-transparent';
        if (type === 'bear') return 'from-red-500/10 via-orange-500/5 to-transparent';
        return 'from-blue-500/10 via-purple-500/5 to-transparent';
    };

    const getIconColor = (type: string) => {
        if (type === 'bull') return 'text-success';
        if (type === 'bear') return 'text-danger';
        return 'text-primary-500';
    };

    return (
        <div className="lite-element">
            <div className={`p-6 rounded-xl bg-gradient-to-br ${getBgGradient(primaryScenario.type)} border border-gray-200 dark:border-zinc-800`}>
                <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className={`flex-shrink-0 w-12 h-12 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 flex items-center justify-center text-2xl ${getIconColor(primaryScenario.type)}`}>
                        {primaryScenario.type === 'bull' ? '📈' :
                            primaryScenario.type === 'bear' ? '📉' : '➡️'}
                    </div>

                    {/* Content */}
                    <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                            {getSimplifiedTitle(primaryScenario.type)}
                        </h3>

                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                            {getSimplifiedMessage(primaryScenario)}
                        </p>

                        {/* Confidence Bar */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-500">AI Confidence</span>
                                <span className={`font-bold ${getIconColor(primaryScenario.type)}`}>
                                    {(primaryScenario.probability * 100).toFixed(0)}%
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-500 ${primaryScenario.type === 'bull' ? 'bg-success' :
                                            primaryScenario.type === 'bear' ? 'bg-danger' :
                                                'bg-primary-500'
                                        }`}
                                    style={{ width: `${primaryScenario.probability * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Key Level (if available) */}
                        {(primaryScenario.target_zone || primaryScenario.invalidation_level) && (
                            <div className="mt-4 p-3 rounded-lg bg-white/50 dark:bg-zinc-900/50 border border-gray-200 dark:border-zinc-800">
                                <div className="text-xs text-gray-500 mb-1">Key Level to Watch</div>
                                <div className="text-sm font-bold text-gray-900 dark:text-white font-mono">
                                    {primaryScenario.target_zone || primaryScenario.invalidation_level}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer Notice */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-zinc-800 text-xs text-gray-500 text-center">
                    💡 Upgrade to Pro mode for detailed scenario breakdown
                </div>
            </div>
        </div>
    );
}
